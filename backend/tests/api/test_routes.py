import pytest
from unittest.mock import MagicMock, AsyncMock

def test_generate_draft_endpoint(client, mock_draft_agent):
    response = client.post("/api/v1/agents/draft", json={
        "subject": "Test",
        "sender": "user@example.com",
        "body": "Hello",
        "instructions": "Reply"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["draft_text"] == "API Mocked Draft"
    assert data["status"] == "generated"

def test_send_email_endpoint(client, mock_google_service):
    response = client.post("/api/v1/agents/send-email", json={
        "recipient": "test@example.com",
        "subject": "Subject",
        "body": "Body"
    })
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_google_service.send_email.assert_called_once()

def test_get_knowledge_docs(client):
    with MagicMock() as mock_ks:
        mock_ks.get_all_documents.return_value = [{"title": "doc1", "path": "doc1.md"}, {"title": "doc2", "path": "doc2.md"}]
        # Since knowledge_service is imported, we might need to monkeypatch it where used
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("api.knowledge_routes.knowledge_service", mock_ks)
            response = client.get("/api/v1/knowledge/docs")
            assert response.status_code == 200
            assert response.json() == [{"title": "doc1", "path": "doc1.md"}, {"title": "doc2", "path": "doc2.md"}]

def test_get_dashboard_status(client):
    # Mock scheduler_service.get_system_health (async method)
    mock_ss = MagicMock()
    mock_ss.get_system_health = AsyncMock(return_value={"status": "Healthy"})
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("api.routes.scheduler_service", mock_ss)
        response = client.get("/api/v1/dashboard/status")
        assert response.status_code == 200
        assert response.json() == {"status": "Healthy"}
