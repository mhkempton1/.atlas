import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

@pytest.fixture
def client(db):
    from core.app import app
    from database.database import get_db
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)

@patch("services.knowledge_service.KnowledgeService.get_all_documents")
def test_get_docs(mock_get_all, client):
    mock_get_all.return_value = [{"title": "Test Doc", "id": "1", "category": "test"}]
    response = client.get("/api/v1/knowledge/docs")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test Doc"

@patch("services.knowledge_service.KnowledgeService.get_document_content")
def test_get_content(mock_get_content, client):
    mock_get_content.return_value = "# Content"
    response = client.get("/api/v1/knowledge/content?path=test/path.md")
    assert response.status_code == 200
    assert response.json()["content"] == "# Content"

@patch("services.knowledge_service.KnowledgeService.get_document_content")
def test_get_content_404(mock_get_content, client):
    mock_get_content.return_value = None
    response = client.get("/api/v1/knowledge/content?path=invalid.md")
    assert response.status_code == 404

@patch("services.search_service.SearchService.search")
def test_search(mock_search, client):
    mock_search.return_value = [{"title": "Result", "score": 0.9}]
    response = client.get("/api/v1/knowledge/search?q=test")
    assert response.status_code == 200
    assert len(response.json()) == 1

@patch("services.knowledge_service.KnowledgeService.get_all_documents")
def test_reindex(mock_get_all, client):
    mock_get_all.return_value = []
    response = client.post("/api/v1/knowledge/reindex")
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
