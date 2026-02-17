from datetime import datetime, timedelta, timezone, time
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Task
from typing import Dict, List, Any

class DigestService:
    def generate_daily_digest(self, db: Session, user_id: int = None) -> Dict[str, Any]:
        """
        Generates a daily task digest.
        """
        now = datetime.now(timezone.utc)
        today = now.date()
        today_start = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, time.max).replace(tzinfo=timezone.utc)

        week_end = today_end + timedelta(days=6)

        yesterday = today - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, time.min).replace(tzinfo=timezone.utc)
        yesterday_end = datetime.combine(yesterday, time.max).replace(tzinfo=timezone.utc)

        # Helper to format task
        def format_task(t):
            return {
                "task_id": t.task_id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project_id": t.project_id
            }

        # Query Due Today
        # Due date is today AND status is not completed/done/cancelled
        due_today_tasks = db.query(Task).filter(
            Task.due_date >= today_start,
            Task.due_date <= today_end,
            Task.status.notin_(["completed", "done", "cancelled"])
        ).all()

        # Query Due This Week
        # Due date is within next 7 days AND status is not completed/done/cancelled
        due_this_week_tasks = db.query(Task).filter(
            Task.due_date >= today_start,
            Task.due_date <= week_end,
            Task.status.notin_(["completed", "done", "cancelled"])
        ).all()

        # Query Overdue
        # Due date is before today AND status is not completed/done/cancelled
        overdue_tasks = db.query(Task).filter(
            Task.due_date < today_start,
            Task.status.notin_(["completed", "done", "cancelled"])
        ).all()

        # Query Completed Yesterday
        # Completed at is yesterday
        completed_yesterday_tasks = db.query(Task).filter(
            Task.completed_at >= yesterday_start,
            Task.completed_at <= yesterday_end
        ).all()

        return {
            "due_today": [format_task(t) for t in due_today_tasks],
            "due_this_week": [format_task(t) for t in due_this_week_tasks],
            "overdue": [format_task(t) for t in overdue_tasks],
            "completed_yesterday": [format_task(t) for t in completed_yesterday_tasks]
        }

digest_service = DigestService()
