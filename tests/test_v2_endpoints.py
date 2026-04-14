"""
Tests for /api/v2/* JSON endpoints.

GCP services (Firebase Admin, Firestore, GCS, google.auth) are patched at
module-import time so the test environment needs no GCP credentials.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


_FAKE_UID = "test-uid-123"
_FAKE_PROJECT = "YOUR_PROJECT_ID"


def _auth_mock():
    m = MagicMock()
    m.verify_id_token.return_value = {"uid": _FAKE_UID}
    return m


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient with all GCP calls mocked out."""
    import firebase_admin.auth  # ensure attribute exists on the module before patching
    with (
        patch.dict(os.environ, {"GCS_BUCKET": "test-bucket", "CORS_ORIGINS": "http://localhost"}),
        patch("google.auth.default", return_value=(MagicMock(), _FAKE_PROJECT)),
        patch("firebase_admin.initialize_app"),
        patch("firebase_admin.auth", _auth_mock()),
        patch("google.cloud.firestore.Client", return_value=MagicMock()),
        patch("google.cloud.storage.Client", return_value=MagicMock()),
    ):
        from fastapi.testclient import TestClient
        import main
        return TestClient(main.app)


AUTH = "Bearer valid-token"


# ── GET /api/v2/items ─────────────────────────────────────────────────────────

def test_list_items_no_auth(client):
    res = client.get("/api/v2/items")
    assert res.status_code == 401


def test_list_items_returns_list(client):
    doc = MagicMock()
    doc.id = "item1"
    doc.to_dict.return_value = {"name": "National ID 123", "region": "me-central2"}

    with patch("main.db") as mock_db:
        (mock_db.collection.return_value
         .document.return_value
         .collection.return_value
         .stream.return_value) = [doc]
        res = client.get("/api/v2/items", headers={"Authorization": AUTH})

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data[0] == {"id": "item1", "name": "National ID 123", "region": "me-central2"}


# ── POST /api/v2/items ────────────────────────────────────────────────────────

def test_create_item_no_auth(client):
    res = client.post("/api/v2/items", json={"name": "Test"})
    assert res.status_code == 401


def test_create_item_empty_name_rejected(client):
    with patch("main.db"):
        res = client.post("/api/v2/items", json={"name": "  "}, headers={"Authorization": AUTH})
    assert res.status_code == 422


def test_create_item_returns_document(client):
    mock_ref = MagicMock()
    mock_ref.id = "new-item-id"

    with patch("main.db") as mock_db:
        (mock_db.collection.return_value
         .document.return_value
         .collection.return_value
         .document.return_value) = mock_ref
        res = client.post("/api/v2/items", json={"name": "National ID 12345"}, headers={"Authorization": AUTH})

    assert res.status_code == 200
    data = res.json()
    assert data == {"id": "new-item-id", "name": "National ID 12345", "region": "me-central2"}


# ── GET /api/v2/items/{item_id}/documents ─────────────────────────────────────

def test_list_documents_no_auth(client):
    res = client.get("/api/v2/items/item1/documents")
    assert res.status_code == 401


def test_list_documents_returns_list(client):
    doc = MagicMock()
    doc.id = "doc1"
    ts = datetime(2026, 4, 14, 10, 0, 0, tzinfo=timezone.utc)
    doc.to_dict.return_value = {
        "gcs_object": "gs://YOUR_BUCKET_NAME/users/uid/items/item1/uuid/file.pdf",
        "original_filename": "file.pdf",
        "content_type": "application/pdf",
        "size_bytes": 2048,
        "uploaded_at": ts,
        "status": "uploaded",
    }

    with patch("main.db") as mock_db:
        (mock_db.collection.return_value
         .document.return_value
         .collection.return_value
         .document.return_value
         .collection.return_value
         .stream.return_value) = [doc]
        res = client.get("/api/v2/items/item1/documents", headers={"Authorization": AUTH})

    assert res.status_code == 200
    data = res.json()
    assert data[0]["id"] == "doc1"
    assert data[0]["original_filename"] == "file.pdf"
    assert data[0]["status"] == "uploaded"
    assert data[0]["uploaded_at"] == ts.isoformat()


# ── POST /api/v2/items/{item_id}/documents ────────────────────────────────────

def test_upload_document_no_auth(client):
    res = client.post(
        "/api/v2/items/item1/documents",
        files={"file": ("test.pdf", b"content", "application/pdf")},
    )
    assert res.status_code == 401


def test_upload_document_item_not_found(client):
    mock_item_ref = MagicMock()
    mock_item_ref.get.return_value.exists = False

    with patch("main.db") as mock_db:
        (mock_db.collection.return_value
         .document.return_value
         .collection.return_value
         .document.return_value) = mock_item_ref
        res = client.post(
            "/api/v2/items/nonexistent/documents",
            files={"file": ("test.pdf", b"content", "application/pdf")},
            headers={"Authorization": AUTH},
        )

    assert res.status_code == 404


def test_upload_document_success(client):
    mock_item_ref = MagicMock()
    mock_item_ref.get.return_value.exists = True
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "new-doc-id"
    mock_item_ref.collection.return_value.document.return_value = mock_doc_ref

    with patch("main.db") as mock_db, patch("main.storage_client") as mock_gcs:
        (mock_db.collection.return_value
         .document.return_value
         .collection.return_value
         .document.return_value) = mock_item_ref
        mock_gcs.bucket.return_value.blob.return_value = MagicMock()

        res = client.post(
            "/api/v2/items/item1/documents",
            files={"file": ("contract.pdf", b"%PDF content", "application/pdf")},
            headers={"Authorization": AUTH},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "new-doc-id"
    assert data["original_filename"] == "contract.pdf"
    assert data["status"] == "uploaded"
    assert data["gcs_object"].startswith("gs://test-bucket/")
