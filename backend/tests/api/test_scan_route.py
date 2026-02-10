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
        message_id="test-msg-scan-001",
        gmail_id="gmail_scan_123",
        from_address="sender@example.com",
        subject="Test Scan Subject",
        body_text="Test body content",
        date_received=datetime.now(),
        synced_at=datetime.now()
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return email

@patch("services.data_api.data_api.add_task")
@patch("services.google_service.google_service")
def test_scan_enqueues_tasks(mock_gs, mock_add_task, client, sample_email):
    # Mock Google Sync to return empty or whatever
    mock_gs.sync_emails.return_value = {"synced": 0}

    response = client.post("/api/v1/email/scan?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["emails_found"] >= 1
    # Tasks created should be empty because it is async
    assert data["tasks_created"] == []

    # Verify add_task was called
    mock_add_task.assert_called()
    call_args = mock_add_task.call_args[1] # kwargs
    assert call_args['type'] == 'analyze_email'
    assert call_args['payload']['email_id'] == sample_email.email_id
