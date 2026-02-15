import pytest
from unittest.mock import patch, MagicMock
from services.notification_service import notification_service
from database.models import Notification
from sqlalchemy.orm import Session

@pytest.fixture
def patch_session(db):
    """
    Patch NotificationService.SessionLocal to use the test 'db' session.
    Mocks commit() to flush() to prevent committing the outer transaction.
    Mocks close() to prevent closing the session prematurely.
    """
    # Create a proxy for the session
    mock_session = MagicMock(wraps=db)

    # Mock commit to just flush, so the outer transaction (managed by 'db' fixture) isn't committed
    mock_session.commit = db.flush

    # Mock close to do nothing, let 'db' fixture handle closure
    mock_session.close = lambda: None

    # Mock query to behave like the real session query
    # MagicMock wraps=db should handle attributes, but methods like query need to be passed through?
    # Actually, wraps=db delegates everything unless overridden.

    # Factory function that returns this mock session
    def get_session():
        return mock_session

    with patch("services.notification_service.SessionLocal", side_effect=get_session):
        yield

def test_push_notification(db, patch_session):
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

    # Verify in DB (using the same session 'db')
    db_notif = db.query(Notification).filter(Notification.id == notif.id).first()
    assert db_notif is not None
    assert db_notif.message == "This is a test notification."

def test_get_unread_notifications(db, patch_session):
    """Test fetching unread notifications."""
    # Create some notifications
    notification_service.push_notification("info", "Read me", "Read msg")
    unread = notification_service.push_notification("alert", "Unread me", "Unread msg")

    # Mark one as read manually
    read_notif = db.query(Notification).filter(Notification.title == "Read me").first()
    read_notif.is_read = True
    db.flush() # Use flush instead of commit because we are in a transaction

    unread_list = notification_service.get_unread_notifications()

    # Check that we found at least the one we created
    # Note: DB might contain data from other tests if rollback failed, but here we assume isolation
    found = [n for n in unread_list if n.id == unread.id]
    assert len(found) == 1
    assert found[0].title == "Unread me"

    # Check that the read one is NOT in the list
    read_found = [n for n in unread_list if n.title == "Read me"]
    assert len(read_found) == 0

def test_mark_as_read(db, patch_session):
    """Test marking a notification as read."""
    notif = notification_service.push_notification("info", "Mark me", "Test msg")

    success = notification_service.mark_as_read(notif.id)
    assert success is True

    # Verify in DB
    updated = db.query(Notification).filter(Notification.id == notif.id).first()
    assert updated.is_read is True
    assert updated.read_at is not None

def test_clear_all(db, patch_session):
    """Test clearing all notifications."""
    notification_service.push_notification("info", "1", "msg")
    notification_service.push_notification("info", "2", "msg")

    count = notification_service.clear_all()
    assert count >= 2

    # Verify DB is empty
    remaining = db.query(Notification).count()
    assert remaining == 0
