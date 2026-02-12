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
        remote_id="gmail_scan_123",
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

@patch("database.database.SessionLocal")
@patch("services.data_api.data_api.add_task")
@patch("services.communication_service.comm_service")
def test_scan_enqueues_tasks(mock_comm, mock_add_task, mock_session_local, client, sample_email, db):
    # Mock Sync to return empty or whatever
    mock_comm.sync_emails.return_value = {"synced": 0}

    # Patch SessionLocal to return the test session
    mock_session_local.return_value = db

    response = client.post("/api/v1/email/scan?limit=5")

    assert response.status_code == 202
    data = response.json()
    assert data["emails_found"] == 0 # The API returns 0 immediately now
    assert data["tasks_created"] == []

    # Verify add_task was called (Background task ran synchronously by TestClient)
    # We need to ensure the query inside run_background_scan found the email.
    # Since we reused the db session, it should see the committed email.

    # Check if add_task was called
    if mock_add_task.called:
        call_args = mock_add_task.call_args[1] # kwargs
        assert call_args['type'] == 'analyze_email'
        assert call_args['payload']['email_id'] == sample_email.email_id
    else:
        # If not called, maybe the query failed or filtered it out.
        # run_background_scan filters by limit=limit.
        # It queries: db.query(Email).order_by(Email.date_received.desc()).limit(limit).all()
        # sample_email should be there.
        pytest.fail("add_task was not called")
