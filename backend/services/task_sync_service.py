from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from dateutil import parser as date_parser

from database.models import Task
from services.altimeter_service import altimeter_service
from services.notification_service import notification_service
from services.task_persistence_service import task_persistence_service

class TaskSyncService:
    def sync_tasks_from_altimeter(self, project_id: str, db: Session):
        """
        Syncs tasks from Altimeter for a specific project.
        """
        # Fetch tasks from Altimeter
        alt_tasks = altimeter_service.get_project_tasks(project_id)

        for alt_task in alt_tasks:
            self._process_altimeter_task(alt_task, project_id, db)

    def _process_altimeter_task(self, alt_task: Dict[str, Any], project_id: str, db: Session):
        alt_task_id = alt_task.get("id")
        if not alt_task_id:
            return

        # Find existing Atlas task
        atlas_task = db.query(Task).filter(Task.related_altimeter_task_id == alt_task_id).first()

        alt_updated_at_str = alt_task.get("updated_at")
        alt_updated_at = self._parse_datetime(alt_updated_at_str)

        if atlas_task:
            # Check for conflict/update
            if not alt_updated_at:
                return # Can't compare

            # Atlas task updated_at
            atlas_updated_at = atlas_task.updated_at or atlas_task.created_at

            # Ensure timezone awareness for comparison
            if atlas_updated_at and atlas_updated_at.tzinfo is None:
                 atlas_updated_at = atlas_updated_at.replace(tzinfo=timezone.utc)

            if atlas_updated_at and alt_updated_at > atlas_updated_at:
                # Altimeter is newer -> Update Atlas
                self._update_atlas_task(atlas_task, alt_task, db)
            elif atlas_updated_at and atlas_updated_at > alt_updated_at:
                # Atlas is newer -> Conflict
                # Log conflict
                print(f"Conflict: Atlas task {atlas_task.task_id} is newer than Altimeter task {alt_task_id}. Skipping update.")
        else:
            # Create new Atlas task
            self._create_atlas_task(alt_task, project_id, db)

    def _create_atlas_task(self, alt_task: Dict[str, Any], project_id: str, db: Session):
        task_data = {
            "title": alt_task.get("name"),
            "status": self._map_status(alt_task.get("status")),
            "project_id": project_id,
            "related_altimeter_task_id": alt_task.get("id"),
            "source": "altimeter",
            "description": f"Imported from Altimeter Project {project_id}",
            "priority": "medium" # Default
        }
        task_persistence_service.persist_task_to_database(task_data, db)

    def _update_atlas_task(self, atlas_task: Task, alt_task: Dict[str, Any], db: Session):
        changes = []
        new_status = self._map_status(alt_task.get("status"))
        new_title = alt_task.get("name")

        if atlas_task.status != new_status:
            changes.append(f"status -> {new_status}")
            atlas_task.status = new_status

        if atlas_task.title != new_title:
            changes.append(f"title -> {new_title}")
            atlas_task.title = new_title

        if changes:
            db.commit()
            db.refresh(atlas_task)

            # Notify
            change_str = ", ".join(changes)
            notification_service.push_notification(
                type="task",
                title=f"Task '{atlas_task.title}' updated from Altimeter",
                message=f"Changes: {change_str}",
                priority="medium",
                link=f"/tasks/{atlas_task.task_id}"
            )

    def _map_status(self, alt_status: str) -> str:
        if not alt_status:
            return "open"
        s = alt_status.lower()
        if s in ["completed", "done", "finished"]:
            return "done"
        if s in ["in progress", "started", "active"]:
            return "in_progress"
        return "open"

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            dt = date_parser.parse(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except:
            return None

task_sync_service = TaskSyncService()
