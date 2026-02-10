from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import TaskQueue
import datetime

class DataAPI:
    def get_db(self):
        """Yields a database session"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def add_task(self, type: str, payload: Dict[str, Any], priority: int = 0) -> int:
        """Adds a task to the queue."""
        db = SessionLocal()
        try:
            task = TaskQueue(
                type=type,
                payload=payload,
                priority=priority,
                status="pending"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task.id
        except Exception as e:
            print(f"[DataAPI] Error adding task: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def claim_next_task(self, type: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Atomically claims the next highest priority pending task of a given type.
        Returns the task dict or None.
        """
        from sqlalchemy import text
        db = SessionLocal()
        try:
            # Use SQLite-compatible atomic UPDATE
            # 1. Select ID (Optimistic locking not needed if we rely on UPDATE affecting 0 rows if claimed)
            # However, to prioritize, we need to pick one.
            # We use a transaction to ensure atomicity.

            # Using RETURNING clause (Supported in SQLite 3.35+)
            # If strictly needed for older versions, we would need to lock the table.
            # Assuming modern SQLite given the environment.

            now = datetime.datetime.now()

            # Subquery to find the best candidate
            subquery = f"""
                SELECT id FROM task_queue
                WHERE type = :type AND status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """

            stmt = text(f"""
                UPDATE task_queue
                SET status = 'processing', agent_id = :agent_id, processed_at = :now
                WHERE id = ({subquery})
                RETURNING id, type, payload, priority, created_at
            """)

            result = db.execute(stmt, {"type": type, "agent_id": agent_id, "now": now}).fetchone()
            db.commit()

            if result:
                return {
                    "id": result.id,
                    "type": result.type,
                    "payload": result.payload, # SQLAlchemy might return this as string or dict depending on driver
                    "priority": result.priority,
                    "created_at": result.created_at
                }
            return None

        except Exception as e:
            db.rollback()
            print(f"[DataAPI] Error claiming task: {e}")
            return None
        finally:
            db.close()

    def complete_task(self, task_id: int, result: Optional[Dict[str, Any]] = None):
        """Marks a task as completed."""
        db = SessionLocal()
        try:
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if task:
                task.status = "completed"
                # Optionally append result to payload or log it?
                # For now just update status.
                if result:
                     # Merge result into payload if needed, or just log
                     pass
                db.commit()
        finally:
            db.close()

    def fail_task(self, task_id: int, error: str):
         db = SessionLocal()
         try:
             task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
             if task:
                 task.status = "failed"
                 task.error_message = error
                 db.commit()
         finally:
             db.close()

    def create_project_task(self, task_data: Dict[str, Any]) -> int:
        """
        Creates a new Task in the project management table (not the queue).
        Funnels agent outputs to the persistence layer.
        """
        from database.models import Task
        db = SessionLocal()
        try:
            new_task = Task(**task_data)
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            return new_task.task_id
        finally:
            db.close()

    def create_calendar_event(self, event_data: Dict[str, Any]) -> int:
        """Creates a new Calendar Event."""
        from database.models import CalendarEvent
        db = SessionLocal()
        try:
            new_event = CalendarEvent(**event_data)
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            return new_event.event_id
        finally:
            db.close()

data_api = DataAPI()
