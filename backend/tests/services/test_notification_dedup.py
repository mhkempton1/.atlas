import pytest
from unittest.mock import patch, MagicMock
from services.notification_service import notification_service
from database.models import Notification
from datetime import datetime, timedelta

@pytest.fixture
def patch_session(db):
    mock_session = MagicMock(wraps=db)
    mock_session.commit = db.flush
    mock_session.close = lambda: None

    def get_session():
        return mock_session

    with patch("services.notification_service.SessionLocal", side_effect=get_session):
        yield

def test_deduplication(db, patch_session):
    # First push
    n1 = notification_service.push_notification("info", "Dedup Test", "Message 1")
    assert n1 is not None

    # Second push (should be duplicate)
    n2 = notification_service.push_notification("info", "Dedup Test", "Message 2") # Message differs, but title/type same

    assert n2.id == n1.id
    assert n2.message == "Message 1" # Should return the existing one

    # Verify only one in DB
    count = db.query(Notification).filter(Notification.title == "Dedup Test").count()
    assert count == 1

def test_no_deduplication_different_title(db, patch_session):
    n1 = notification_service.push_notification("info", "Title 1", "Message 1")
    n2 = notification_service.push_notification("info", "Title 2", "Message 2")

    assert n1.id != n2.id

    assert db.query(Notification).filter(Notification.title == "Title 1").count() == 1
    assert db.query(Notification).filter(Notification.title == "Title 2").count() == 1

def test_expired_deduplication(db, patch_session):
    # Simulate an old notification
    old_notif = Notification(
        type="info",
        title="Old Notification",
        message="Old Msg",
        created_at=datetime.now() - timedelta(minutes=6),
        is_read=False
    )
    db.add(old_notif)
    db.flush() # Flush to assign ID

    # Push a new one with same title/type
    new_notif = notification_service.push_notification("info", "Old Notification", "New Msg")

    assert new_notif.id != old_notif.id
    assert new_notif.message == "New Msg"

    count = db.query(Notification).filter(Notification.title == "Old Notification").count()
    assert count == 2
