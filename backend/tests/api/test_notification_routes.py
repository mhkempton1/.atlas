import pytest
from database.models import Notification
from unittest.mock import patch
from sqlalchemy.orm import Session
import logging

@pytest.fixture
def patch_session(db):
    """
    Patch NotificationService.SessionLocal to use the same connection as the test 'db' fixture.
    """
    def get_session():
        return Session(bind=db.bind)

    with patch("services.notification_service.SessionLocal", side_effect=get_session) as mock:
        yield mock

def test_get_notifications(client, db, patch_session):
    # Setup
    n1 = Notification(type="task", title="N1", message="M1", is_read=False)
    n2 = Notification(type="task", title="N2", message="M2", is_read=True)
    db.add(n1)
    db.add(n2)
    db.commit()

    # Test list unread only (default)
    response = client.get("/api/v1/notifications/list")
    assert response.status_code == 200
    data = response.json()

    titles = [item["title"] for item in data]
    assert "N1" in titles
    assert "N2" not in titles

    response = client.get("/api/v1/notifications/list?unread_only=false")
    assert response.status_code == 200
    data = response.json()
    titles = [item["title"] for item in data]
    assert "N1" in titles
    assert "N2" in titles

def test_mark_notification_read(client, db, patch_session):
    n1 = Notification(type="task", title="UniqueUnread", message="M", is_read=False)
    db.add(n1)
    db.commit()

    response = client.patch(f"/api/v1/notifications/{n1.id}/read")
    assert response.status_code == 200
    assert response.json()["success"] is True

    db.expire_all()
    updated = db.query(Notification).filter(Notification.id == n1.id).first()
    assert updated.is_read is True

def test_clear_notifications(client, db, patch_session):
    db.add(Notification(type="t", title="ClearMe1", message="m", is_read=False))
    db.add(Notification(type="t", title="ClearMe2", message="m", is_read=True))
    db.commit()

    response = client.delete("/api/v1/notifications/clear")
    assert response.status_code == 200
    assert response.json()["cleared_count"] >= 2

    db.expire_all()
    count = db.query(Notification).count()
    assert count == 0

def test_mark_nonexistent_read(client, patch_session):
    response = client.patch("/api/v1/notifications/999999/read")
    assert response.status_code == 404
