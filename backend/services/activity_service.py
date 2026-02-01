from datetime import datetime
from typing import List, Dict, Any, Optional
from database.database import SessionLocal
from database.models import SystemActivity
from sqlalchemy import desc

class ActivityService:
    @staticmethod
    def log_activity(type: str, action: str, target: str, details: Optional[str] = None):
        """
        Create a new system activity log entry.
        """
        db = SessionLocal()
        try:
            new_activity = SystemActivity(
                type=type,
                action=action,
                target=target,
                details=details,
                timestamp=datetime.now()
            )
            db.add(new_activity)
            db.commit()
            print(f"Logged activity: {type} - {action} - {target}")
        except Exception as e:
            print(f"Failed to log activity: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def get_recent_activity(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch recent activity logs, newest first.
        """
        db = SessionLocal()
        try:
            activities = db.query(SystemActivity).order_by(desc(SystemActivity.timestamp)).limit(limit).all()
            return [
                {
                    "id": a.activity_id,
                    "type": a.type,
                    "action": a.action,
                    "target": a.target,
                    "details": a.details,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in activities
            ]
        finally:
            db.close()

activity_service = ActivityService()
