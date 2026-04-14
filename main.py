import logging
import uuid
import google.auth
from fastapi import FastAPI, Header, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth, initialize_app
from google.cloud import firestore
from google.cloud import storage as gcs
from google.api_core.client_options import ClientOptions

logging.basicConfig(level=logging.INFO)

_, _project_id = google.auth.default()
logging.info("Detected GCP project: %s", _project_id)

app = FastAPI()
initialize_app(options={"projectId": _project_id})

# 1. ALLOW CORS FOR FIREBASE HOSTING DOMAINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://YOUR_PROJECT_ID.web.app",
        "https://YOUR_PROJECT_ID.firebaseapp.com",
        "https://YOUR_VUE_SITE_ID.web.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ENSURE REGIONAL ENDPOINT FOR KSA COMPLIANCE
ENDPOINT = "firestore.me-central2.rep.googleapis.com:443"
db = firestore.Client(
    database="pii-records", client_options=ClientOptions(api_endpoint=ENDPOINT)
)

# GCS bucket for document storage — me-central2 for KSA data residency.
# Bucket location (me-central2) enforces data residency; all objects stay in Dammam.
GCS_BUCKET = "YOUR_BUCKET_NAME"
storage_client = gcs.Client()


async def verify_user(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing ID Token")
    try:
        id_token = authorization.split(" ")[1]
        logging.info("verify_id_token: token_prefix=%s len=%d", id_token[:20], len(id_token))
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        logging.error("verify_id_token failed: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=401, detail=f"Unauthorized: {type(e).__name__}: {e}")


@app.get("/api/items")
async def read_items(authorization: str = Header(None)):
    uid = await verify_user(authorization)
    docs = db.collection("users").document(uid).collection("items").stream()
    items = [{"id": d.id, **d.to_dict()} for d in docs]

    if not items:
        return HTMLResponse(
            content="<li class='text-slate-400 py-4 text-center'>No records found in Dammam.</li>"
        )

    html = "".join(
        [
            f"<li class='flex justify-between p-3 bg-white border border-slate-100 mb-2 rounded shadow-sm'><span class='font-medium text-slate-700'>{i['name']}</span><span class='text-[10px] bg-slate-100 px-2 py-1 rounded font-bold uppercase'>{i.get('region', 'KSA')}</span></li>"
            for i in items
        ]
    )
    return HTMLResponse(content=html)


@app.post("/api/items")
async def create_item(request: Request, authorization: str = Header(None)):
    uid = await verify_user(authorization)
    form = await request.form()
    item_name = form.get("item_name")

    doc_ref = db.collection("users").document(uid).collection("items").document()
    doc_ref.set({"name": item_name, "region": "me-central2"})
    return HTMLResponse(
        content=f"<li class='flex justify-between p-3 bg-green-50 border border-green-200 mb-2 rounded animate-pulse'><span>{item_name}</span><span class='text-xs text-green-600 font-bold'>SAVED</span></li>"
    )


# ─── v2 JSON endpoints (Vue frontend) ────────────────────────────────────────

@app.get("/api/v2/items")
async def list_items_json(authorization: str = Header(None)):
    uid = await verify_user(authorization)
    docs = db.collection("users").document(uid).collection("items").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        items.append({"id": d.id, "name": data.get("name"), "region": data.get("region")})
    return items


@app.post("/api/v2/items")
async def create_item_json(request: Request, authorization: str = Header(None)):
    uid = await verify_user(authorization)
    body = await request.json()
    item_name = body.get("name", "").strip()
    if not item_name:
        raise HTTPException(status_code=422, detail="name is required")

    doc_ref = db.collection("users").document(uid).collection("items").document()
    doc_ref.set({"name": item_name, "region": "me-central2"})
    return {"id": doc_ref.id, "name": item_name, "region": "me-central2"}


@app.get("/api/v2/items/{item_id}/documents")
async def list_documents(item_id: str, authorization: str = Header(None)):
    uid = await verify_user(authorization)
    docs = (
        db.collection("users").document(uid)
          .collection("items").document(item_id)
          .collection("documents").stream()
    )
    return [
        {
            "id": d.id,
            **{k: v for k, v in d.to_dict().items() if k != "uploaded_at"},
            "uploaded_at": d.to_dict().get("uploaded_at").isoformat()
                           if d.to_dict().get("uploaded_at") else None,
        }
        for d in docs
    ]


@app.post("/api/v2/items/{item_id}/documents")
async def upload_document(
    item_id: str,
    file: UploadFile = File(...),
    authorization: str = Header(None),
):
    uid = await verify_user(authorization)

    item_ref = (
        db.collection("users").document(uid)
          .collection("items").document(item_id)
    )
    if not item_ref.get().exists:
        raise HTTPException(status_code=404, detail="Item not found")

    unique_id = str(uuid.uuid4())
    blob_name = f"users/{uid}/items/{item_id}/{unique_id}/{file.filename}"

    content = await file.read()
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type=file.content_type)

    logging.info(
        "Uploaded document: bucket=%s blob=%s size=%d uid=%s item=%s",
        GCS_BUCKET, blob_name, len(content), uid, item_id,
    )

    doc_ref = item_ref.collection("documents").document()
    doc_ref.set({
        "gcs_object": f"gs://{GCS_BUCKET}/{blob_name}",
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "uploaded_at": firestore.SERVER_TIMESTAMP,
        "status": "uploaded",
    })

    return {
        "id": doc_ref.id,
        "gcs_object": f"gs://{GCS_BUCKET}/{blob_name}",
        "original_filename": file.filename,
        "status": "uploaded",
    }
