import pytest
from unittest.mock import patch
from database.models import Notification
from services.notification_service import notification_service

@pytest.fixture(autouse=True)
def patch_notification_service_db(db):
    """
    Patch SessionLocal in notification_service to use the test session.
    Prevent the service from closing the session, so we can verify data.
    """
    # Mock close to prevent service from closing the session
    original_close = db.close
    db.close = lambda: None

    with patch("services.notification_service.SessionLocal", return_value=db):
        yield

    # Restore close so the fixture can clean up
    db.close = original_close

def test_get_notifications_empty(client):
    response = client.get("/api/v1/notifications/list")
    assert response.status_code == 200
    assert response.json() == []

def test_create_and_get_notification(client, db):
    # Create via service directly (simulating a background task or other service)
    notification = notification_service.push_notification(
        type="test",
        title="Test Notification",
        message="This is a test",
        priority="high"
    )

    # Verify via API
    response = client.get("/api/v1/notifications/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == notification.id
    assert data[0]["title"] == "Test Notification"
    assert data[0]["priority"] == "high"
    assert data[0]["is_read"] is False

def test_mark_notification_read(client, db):
    # Create notification
    notification = notification_service.push_notification(
        type="test",
        title="Test Read",
        message="Message"
    )

    # Mark as read
    response = client.patch(f"/api/v1/notifications/{notification.id}/read")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify it's read in DB
    db.refresh(notification)
    assert notification.is_read is True

    # Verify API list (unread_only=True by default)
    response = client.get("/api/v1/notifications/list")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Verify API list (unread_only=False)
    response = client.get("/api/v1/notifications/list?unread_only=false")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["is_read"] is True

def test_clear_notifications(client, db):
    # Create notifications
    notification_service.push_notification(type="t1", title="N1", message="M1")
    notification_service.push_notification(type="t2", title="N2", message="M2")

    response = client.delete("/api/v1/notifications/clear")
    assert response.status_code == 200
    assert response.json()["cleared_count"] == 2

    # Verify empty
    response = client.get("/api/v1/notifications/list?unread_only=false")
    assert len(response.json()) == 0

    # Verify DB
    assert db.query(Notification).count() == 0
