from datetime import datetime
from typing import List, Optional, Dict, Any
from database.database import SessionLocal
from database.models import Notification

class NotificationService:
    """Service for handling persistent system-wide notifications."""

    def push_notification(
        self, 
        type: str, 
        title: str, 
        message: str, 
        priority: str = "medium", 
        link: Optional[str] = None
    ) -> Notification:
        """Create and persist a new notification."""
        db = SessionLocal()
        try:
            notification = Notification(
                type=type,
                title=title,
                message=message,
                priority=priority,
                link=link,
                created_at=datetime.now(),
                is_read=False
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification
        finally:
            db.close()

    def get_unread_notifications(self, limit: int = 50) -> List[Notification]:
        """Fetch unread notifications."""
        db = SessionLocal()
        try:
            return db.query(Notification).filter(
                Notification.is_read == False
            ).order_by(Notification.created_at.desc()).limit(limit).all()
        finally:
            db.close()

    def mark_as_read(self, notification_id: int) -> bool:
        """Mark a notification as read."""
        db = SessionLocal()
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                notification.is_read = True
                notification.read_at = datetime.now()
                db.commit()
                return True
            return False
        finally:
            db.close()

    def clear_all(self) -> int:
        """Delete all notifications (or mark all as read/archive)."""
        db = SessionLocal()
        try:
            count = db.query(Notification).delete()
            db.commit()
            return count
        finally:
            db.close()

# Singleton instance
notification_service = NotificationService()
