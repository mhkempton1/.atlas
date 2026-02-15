import pytest
from fastapi.testclient import TestClient
from database.models import Contact
from datetime import datetime, timezone

@pytest.fixture
def client(db):
    from core.app import app
    from database.database import get_db
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)

@pytest.fixture
def sample_contact(db):
    contact = Contact(
        email_address="test@example.com",
        name="Test User",
        company="Test Corp",
        phone="123-456-7890",
        title="Developer",
        relationship_type="vendor",
        email_count=5,
        last_contact_date=datetime.now(timezone.utc),
        tags=["vip", "urgent"],
        altimeter_vendor_id=101
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

def test_search_contact_found(client, sample_contact):
    response = client.get("/api/v1/contacts/search?q=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email_address"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["company"] == "Test Corp"
    assert data["relationship_type"] == "vendor"
    assert data["altimeter_vendor_id"] == 101
    assert "vip" in data["tags"]

def test_search_contact_not_found(client, db):
    response = client.get("/api/v1/contacts/search?q=unknown@example.com")
    assert response.status_code == 200
    assert response.json() is None

def test_search_contact_case_insensitive(client, sample_contact):
    response = client.get("/api/v1/contacts/search?q=TEST@EXAMPLE.COM")
    assert response.status_code == 200
    data = response.json()
    assert data["email_address"] == "test@example.com"

def test_search_contact_invalid_query(client):
    response = client.get("/api/v1/contacts/search?q=ab")
    assert response.status_code == 422 # Min length is 3
