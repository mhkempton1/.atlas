import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

@pytest.fixture
def client(db):
    from core.app import app
    from database.database import get_db
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)

@pytest.fixture
def sample_email(db):
    from database.models import Email
    from datetime import datetime
    email = Email(
        message_id="test-msg-001",
        remote_id="gmail_abc123",
        thread_id="thread_xyz",
        from_address="sender@example.com",
        subject="Test Subject",
        body_text="Test body content",
        date_received=datetime.now(),
        is_read=False,
        synced_at=datetime.now()
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email

def test_get_email_marks_read(client, sample_email):
    response = client.get(f"/api/v1/email/{sample_email.email_id}")
    assert response.status_code == 200
    assert response.json()["is_read"] == True

def test_toggle_star(client, sample_email):
    response = client.post(f"/api/v1/email/{sample_email.email_id}/star")
    assert response.status_code == 200
    assert response.json()["starred"] == True

@patch("services.communication_service.comm_service")
def test_delete_email(mock_comm, client, sample_email):
    mock_comm.trash_email.return_value = {"success": True}
    response = client.delete(f"/api/v1/email/{sample_email.email_id}")
    assert response.status_code == 200
    assert response.json()["success"] == True
    mock_comm.trash_email.assert_called_once_with("gmail_abc123")

@patch("services.communication_service.comm_service")
def test_archive_email(mock_comm, client, sample_email):
    mock_comm.archive_email.return_value = {"success": True}
    response = client.post(f"/api/v1/email/{sample_email.email_id}/archive")
    assert response.status_code == 200
    assert response.json()["success"] == True

@patch("services.communication_service.comm_service")
def test_reply_to_email(mock_comm, client, sample_email):
    mock_comm.reply_to_email.return_value = {"success": True, "message_id": "new_msg"}
    response = client.post(
        f"/api/v1/email/{sample_email.email_id}/reply",
        json={"body": "Thanks for your email!"}
    )
    assert response.status_code == 200
    assert response.json()["success"] == True

@patch("services.communication_service.comm_service")
def test_forward_email(mock_comm, client, sample_email):
    mock_comm.forward_email.return_value = {"success": True, "message_id": "fwd_msg"}
    response = client.post(
        f"/api/v1/email/{sample_email.email_id}/forward",
        json={"to_address": "other@example.com", "note": "FYI"}
    )
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_mark_unread(client, sample_email, db):
    # First mark as read
    client.get(f"/api/v1/email/{sample_email.email_id}")
    
    with patch("services.communication_service.comm_service") as mock_comm:
        mock_comm.mark_unread.return_value = {"success": True}
        response = client.post(f"/api/v1/email/{sample_email.email_id}/unread")
        assert response.status_code == 200

def test_update_category_nonexistent(client):
    response = client.delete("/api/v1/email/99999")
    assert response.status_code == 404

def test_update_email_category(client, sample_email):
    response = client.put(
        f"/api/v1/email/{sample_email.email_id}/category",
        json={"category": "urgent"}
    )
    assert response.status_code == 200
    assert response.json()["category"] == "urgent"

def test_update_category_nonexistent_real(client):
    response = client.put("/api/v1/email/99999/category", json={"category": "work"})
    assert response.status_code == 404

def test_search_emails(client, db):
    from database.models import Email
    from datetime import datetime, timedelta, timezone

    # 1. Setup Data
    # Clear existing emails to avoid interference from other tests if DB isn't reset
    # (Fixture 'db' usually provides a session, but let's be safe or just rely on unique content)

    email1 = Email(
        message_id="msg1", remote_id="r1", subject="Meeting Update",
        body_text="The meeting is at 10am.", from_address="boss@company.com",
        date_received=datetime.now(timezone.utc) - timedelta(days=1),
        to_addresses=["me@company.com"], labels=["work"],
        is_read=True
    )
    email2 = Email(
        message_id="msg2", remote_id="r2", subject="Lunch?",
        body_text="Want to go to lunch?", from_address="friend@gmail.com",
        date_received=datetime.now(timezone.utc),
        to_addresses=["me@company.com"], labels=["personal"],
        is_read=False
    )
    email3 = Email(
        message_id="msg3", remote_id="r3", subject="Project Update",
        body_text="The project is delayed.", from_address="colleague@company.com",
        date_received=datetime.now(timezone.utc) - timedelta(days=2),
        to_addresses=["team@company.com"], labels=["work", "urgent"],
        is_read=True
    )
    db.add_all([email1, email2, email3])
    db.commit()

    # 2. Test Text Search
    response = client.get("/api/v1/email/search?q=meeting")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    found = any(e['subject'] == "Meeting Update" for e in data)
    assert found

    # Test Body Search
    response = client.get("/api/v1/email/search?q=delayed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    found = any(e['subject'] == "Project Update" for e in data)
    assert found

    # 3. Test Filters
    # From
    response = client.get("/api/v1/email/search?from=boss")
    data = response.json()
    found = any(e['from_address'] == "boss@company.com" for e in data)
    assert found

    # Labels
    response = client.get("/api/v1/email/search?labels=urgent")
    data = response.json()
    found = any(e['subject'] == "Project Update" for e in data)
    assert found

    # Date Range (Only email2 is recent)
    start = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    response = client.get("/api/v1/email/search", params={"date_start": start})
    data = response.json()
    # Should contain Lunch? but not others
    subjects = [e['subject'] for e in data]
    assert "Lunch?" in subjects
    assert "Meeting Update" not in subjects

    # 4. Test Empty
    response = client.get("/api/v1/email/search?q=xyz123_nonexistent")
    assert len(response.json()) == 0

    # 5. Test Pagination
    # We added 3 emails.
    # Depending on what else is in DB, let's just check limit works
    response = client.get("/api/v1/email/search?limit=1")
    assert len(response.json()) == 1

    # 6. Test Invalid Date
    response = client.get("/api/v1/email/search?date_start=invalid-date")
    assert response.status_code == 400
    assert "Invalid date_start format" in response.json()["detail"]
