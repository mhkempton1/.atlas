from sqlalchemy.orm import Session
from database.models import Task
from typing import List, Optional, Dict, Any
import datetime

class TaskPersistenceService:
    def persist_task_to_database(self, task_data: Dict[str, Any], db: Session) -> Task:
        """
        Persist a task to the database.
        Handles deduplication logic if necessary (e.g., checking existing tasks).
        """
        # Map fields
        # Ensure we don't pass extra fields that aren't in the model
        valid_fields = {
            "title", "description", "status", "priority", "category",
            "project_id", "email_id", "due_date", "original_due_date",
            "estimated_hours", "actual_hours", "parent_task_id",
            "created_from", "created_at", "completed_at",
            "source", "assigned_to", "related_altimeter_task_id",
            "is_recurring", "recurrence_pattern", "tags",
            "sync_status", "last_synced_at", "etag", "remote_id"
        }

        filtered_data = {k: v for k, v in task_data.items() if k in valid_fields}

        # Handle defaults
        if "status" not in filtered_data:
            filtered_data["status"] = "open"
        if "priority" not in filtered_data:
            filtered_data["priority"] = "medium"
        if "created_at" not in filtered_data:
            filtered_data["created_at"] = datetime.datetime.now(datetime.timezone.utc)
        if "sync_status" not in filtered_data:
            filtered_data["sync_status"] = "pending" # Default to pending sync for new tasks

        task = Task(**filtered_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_task_status(self, task_id: int, new_status: str, db: Session) -> Optional[Task]:
        """
        Update the status of a task.
        Sets completed_at if status is 'completed' or 'done'.
        """
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None

        old_status = task.status
        task.status = new_status

        if new_status in ["completed", "done", "cancelled"] and old_status not in ["completed", "done", "cancelled"]:
            task.completed_at = datetime.datetime.now(datetime.timezone.utc)
        elif new_status not in ["completed", "done", "cancelled"] and old_status in ["completed", "done", "cancelled"]:
            task.completed_at = None

        # Mark for sync
        task.sync_status = "pending"

        db.commit()
        db.refresh(task)
        return task

    def get_tasks_by_status(self, status: str, db: Session) -> List[Task]:
        """
        Get tasks filtered by status.
        """
        return db.query(Task).filter(Task.status == status).all()

    def get_tasks_by_email(self, email_id: int, db: Session) -> List[Task]:
        """
        Get tasks linked to a specific email.
        """
        return db.query(Task).filter(Task.email_id == email_id).all()

task_persistence_service = TaskPersistenceService()
