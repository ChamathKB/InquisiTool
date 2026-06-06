import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@patch("inquisitool.routes.knowledgebases.create_documents_collection", new_callable=AsyncMock)
def test_create_collection(mock_create, client):
    mock_create.return_value = {"inserted_id": "col-123"}
    response = client.post("/knowledgebases/create_collection?collection_name=test_col")
    assert response.status_code == 200
    assert "col-123" in response.json()["message"]


@patch("inquisitool.routes.knowledgebases.create_documents_collection", new_callable=AsyncMock)
def test_create_collection_failure(mock_create, client):
    mock_create.side_effect = Exception("Qdrant error")
    response = client.post("/knowledgebases/create_collection?collection_name=test_col")
    assert response.status_code == 500


@patch("inquisitool.routes.knowledgebases.upload_document", new_callable=AsyncMock)
def test_upload_docs(mock_upload, client):
    mock_upload.return_value = None
    response = client.post(
        "/knowledgebases/upload_docs",
        data={"collection_id": "col-123"},
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Embeddings uploaded successfully!"


@patch("inquisitool.routes.knowledgebases.upload_document", new_callable=AsyncMock)
def test_upload_docs_failure(mock_upload, client):
    mock_upload.side_effect = Exception("Embedding error")
    response = client.post(
        "/knowledgebases/upload_docs",
        data={"collection_id": "col-123"},
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")},
    )
    assert response.status_code == 500
    assert "Document upload failed" in response.json()["detail"]


@patch("inquisitool.routes.knowledgebases.delete_documents_collection", new_callable=AsyncMock)
def test_delete_collection(mock_delete, client):
    mock_delete.return_value = {"message": "Collection deleted successfully"}
    response = client.delete("/knowledgebases/delete_collection?collection_id=col-123")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]


@patch("inquisitool.routes.knowledgebases.delete_documents_collection", new_callable=AsyncMock)
def test_delete_collection_failure(mock_delete, client):
    mock_delete.side_effect = Exception("Deletion error")
    response = client.delete("/knowledgebases/delete_collection?collection_id=col-123")
    assert response.status_code == 500
    assert "Document deletion failed" in response.json()["detail"]
