import pytest
from services.notification_service import notification_service
from database.models import Notification
from database.database import SessionLocal

@pytest.fixture
def clean_notifications():
    # Cleanup before and after test
    db = SessionLocal()
    try:
        db.query(Notification).delete()
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(Notification).delete()
        db.commit()
    finally:
        db.close()

def test_push_notification(clean_notifications):
    """Test pushing a new notification."""
    notif = notification_service.push_notification(
        type="task",
        title="Test Task",
        message="This is a test notification.",
        priority="high",
        link="/tasks/1"
    )

    assert notif.id is not None
    assert notif.type == "task"
    assert notif.title == "Test Task"
    assert notif.priority == "high"
    assert notif.is_read is False

    # Verify in DB
    db = SessionLocal()
    try:
        db_notif = db.query(Notification).filter(Notification.id == notif.id).first()
        assert db_notif is not None
        assert db_notif.message == "This is a test notification."
    finally:
        db.close()

def test_get_unread_notifications(clean_notifications):
    """Test fetching unread notifications."""
    # Create some notifications
    notification_service.push_notification("info", "Read me", "Read msg")
    unread = notification_service.push_notification("alert", "Unread me", "Unread msg")

    # Mark one as read manually to simulate mixed state
    db = SessionLocal()
    try:
        read_notif = db.query(Notification).filter(Notification.title == "Read me").first()
        read_notif.is_read = True
        db.commit()
    finally:
        db.close()

    unread_list = notification_service.get_unread_notifications()
    assert len(unread_list) == 1
    assert unread_list[0].id == unread.id
    assert unread_list[0].title == "Unread me"

def test_mark_as_read(clean_notifications):
    """Test marking a notification as read."""
    notif = notification_service.push_notification("info", "Mark me", "Test msg")

    success = notification_service.mark_as_read(notif.id)
    assert success is True

    # Verify in DB
    db = SessionLocal()
    try:
        updated = db.query(Notification).filter(Notification.id == notif.id).first()
        assert updated.is_read is True
        assert updated.read_at is not None
    finally:
        db.close()

def test_clear_all(clean_notifications):
    """Test clearing all notifications."""
    notification_service.push_notification("info", "1", "msg")
    notification_service.push_notification("info", "2", "msg")

    count = notification_service.clear_all()
    assert count == 2

    # Verify DB is empty
    db = SessionLocal()
    try:
        remaining = db.query(Notification).count()
        assert remaining == 0
    finally:
        db.close()
