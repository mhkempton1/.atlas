from fastapi.testclient import TestClient
from core.app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "Atlas"
    assert data["ai_enabled"] is True
