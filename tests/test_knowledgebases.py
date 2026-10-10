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
    assert response.json()["collection_id"] == "col-123"


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


@patch("inquisitool.routes.knowledgebases.list_knowledgebases", new_callable=AsyncMock)
def test_list_collections(mock_list, client):
    mock_list.return_value = [
        {"collection_id": "col-123", "collection_name": "test_col", "uploaded_at": "2025-01-01T00:00:00"}
    ]
    response = client.get("/knowledgebases/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@patch("inquisitool.routes.knowledgebases.list_knowledgebases", new_callable=AsyncMock)
def test_list_collections_failure(mock_list, client):
    mock_list.side_effect = Exception("DB error")
    response = client.get("/knowledgebases/")
    assert response.status_code == 500


@patch("inquisitool.routes.knowledgebases.answer_question")
def test_rag_chat_success(mock_answer, client):
    mock_answer.return_value = ("The answer is 42.", [{"text": "chunk text", "score": 0.95}])
    response = client.post(
        "/knowledgebases/chat",
        json={"collection_id": "col-123", "question": "What is the answer?", "history": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The answer is 42."
    assert data["sources"][0]["score"] == 0.95


@patch("inquisitool.routes.knowledgebases.answer_question")
def test_rag_chat_failure(mock_answer, client):
    mock_answer.side_effect = Exception("LLM error")
    response = client.post(
        "/knowledgebases/chat",
        json={"collection_id": "col-123", "question": "What is the answer?"},
    )
    assert response.status_code == 500
