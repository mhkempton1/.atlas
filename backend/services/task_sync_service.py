from sqlalchemy.orm import Session
from database.models import Task, TaskSyncLog
from services.altimeter_service import altimeter_service
from typing import Optional, Dict, Any
import datetime

class TaskSyncService:
    def create_altimeter_task_from_atlas(self, atlas_task_id: int, project_id: Optional[str], db: Session) -> Dict[str, Any]:
        """
        Syncs an Atlas task to Altimeter.
        """
        task = db.query(Task).filter(Task.task_id == atlas_task_id).first()
        if not task:
            raise ValueError(f"Task with ID {atlas_task_id} not found.")

        if not project_id and not task.project_id:
             raise ValueError("Project ID is required for Altimeter sync.")

        target_project_id = project_id if project_id else task.project_id

        # Prepare data for Altimeter
        task_data = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "project_id": target_project_id
        }

        # Sync to Altimeter
        try:
            alt_task_id = altimeter_service.sync_task_to_altimeter(task_data)
        except Exception as e:
            # Log failure?
            raise RuntimeError(f"Failed to sync to Altimeter: {str(e)}")

        # Update Atlas Task
        task.related_altimeter_task_id = alt_task_id
        # If project_id was passed and different, update it?
        # The requirement says "Store returned altimeter_task_id on Atlas task record".
        # It doesn't explicitly say update project_id but it makes sense if it was missing.
        if not task.project_id:
            task.project_id = target_project_id

        # Create Sync Log
        # Serialize datetime objects in task_data for JSON storage
        log_data = task_data.copy()
        if log_data.get("due_date"):
            log_data["due_date"] = log_data["due_date"].isoformat() if isinstance(log_data["due_date"], datetime.datetime) else log_data["due_date"]

        sync_log = TaskSyncLog(
            atlas_task_id=task.task_id,
            altimeter_task_id=alt_task_id,
            sync_direction="atlas_to_altimeter",
            synced_fields=log_data,
            synced_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(sync_log)
        db.commit()
        db.refresh(task)

        return {
            "status": "success",
            "atlas_task_id": task.task_id,
            "altimeter_task_id": alt_task_id
        }

task_sync_service = TaskSyncService()
