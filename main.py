import logging
import os
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
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
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
GCS_BUCKET = os.environ["GCS_BUCKET"]
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
    result = []
    for d in docs:
        data = d.to_dict()
        uploaded_at = data.pop("uploaded_at", None)
        result.append({
            "id": d.id,
            **data,
            "uploaded_at": uploaded_at.isoformat() if uploaded_at else None,
        })
    return result


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
    safe_filename = os.path.basename(file.filename or "upload").replace(" ", "_") or "upload"
    blob_name = f"users/{uid}/items/{item_id}/{unique_id}/{safe_filename}"

    content = await file.read()
    MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB maximum")
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
