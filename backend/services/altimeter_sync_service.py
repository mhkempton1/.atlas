import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import SessionLocal
from database.models import Task, SyncQueue, SyncActivityLog, SyncConflict
from services.altimeter_api_service import altimeter_api_service

# Configure logging
logger = logging.getLogger("altimeter_sync")
logger.setLevel(logging.INFO)

class AltimeterSyncService:
    def __init__(self):
        self.is_running = False
        self._ws_manager = None

    def set_ws_manager(self, manager):
        self._ws_manager = manager

    async def start_worker(self):
        """Starts the background sync worker."""
        if self.is_running:
            return
        self.is_running = True
        logger.info("Altimeter Sync Worker started.")
        while self.is_running:
            try:
                await self.process_queue()
            except Exception as e:
                logger.error(f"Error in sync worker loop: {e}")
            await asyncio.sleep(2) # Poll every 2 seconds

    def stop_worker(self):
        self.is_running = False
        logger.info("Altimeter Sync Worker stopped.")

    async def process_queue(self):
        """Polls the queue and processes pending items."""
        db = SessionLocal()
        try:
            # Fetch pending items that are ready (considering backoff)
            items = db.query(SyncQueue).filter(
                or_(SyncQueue.status == 'pending', SyncQueue.status == 'retry')
            ).all()

            for item in items:
                # Check backoff if retry
                if item.status == 'retry':
                    backoff_seconds = 5 * (5 ** (item.retry_count - 1)) if item.retry_count > 0 else 5
                    if item.last_attempt:
                        # Ensure timezone awareness
                        last_attempt = item.last_attempt
                        if last_attempt.tzinfo is None:
                            last_attempt = last_attempt.replace(tzinfo=timezone.utc)

                        next_attempt = last_attempt + timedelta(seconds=backoff_seconds)
                        now = datetime.now(timezone.utc)

                        if now < next_attempt:
                            continue

                await self._process_item(item, db)

        finally:
            db.close()

    async def _process_item(self, item: SyncQueue, db: Session):
        """Processes a single sync queue item."""
        logger.info(f"Processing sync item {item.id}: {item.direction} {item.entity_type} {item.entity_id}")

        item.status = 'syncing'
        item.last_attempt = datetime.now(timezone.utc)
        db.commit()

        # Notify UI
        if self._ws_manager:
            await self._ws_manager.broadcast_sync_status(item.entity_type, item.entity_id, "syncing")

        try:
            if item.entity_type == 'task':
                if item.direction == 'push':
                    await self._sync_push_task(item, db)
                elif item.direction == 'pull':
                    await self._sync_pull_task(item, db)

            # If status wasn't changed to conflict during processing, mark as synced
            if item.status != 'conflict':
                item.status = 'synced'
                item.error_message = None
                # Log success
                self._log_history(db, item, "success")
                db.commit()

                # Notify UI
                if self._ws_manager:
                    await self._ws_manager.broadcast_sync_status(item.entity_type, item.entity_id, "synced")
            else:
                 self._log_history(db, item, "conflict")
                 db.commit()

        except Exception as e:
            logger.error(f"Sync failed for item {item.id}: {e}")
            item.retry_count += 1
            item.error_message = str(e)

            if item.retry_count >= 3:
                item.status = 'failed'
                self._log_history(db, item, "failed", str(e))
                if self._ws_manager:
                    await self._ws_manager.broadcast_sync_status(item.entity_type, item.entity_id, "error")
            else:
                item.status = 'retry'

            db.commit()

    async def _sync_push_task(self, item: SyncQueue, db: Session):
        """Pushes a local task to Altimeter."""
        task = db.query(Task).filter(Task.task_id == item.entity_id).first()
        if not task:
            raise ValueError(f"Task {item.entity_id} not found")

        task_data = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "atlas_id": task.task_id,
            "project_id": task.project_id
        }

        # If we have a remote_id, update. Else create.
        if task.remote_id:
            await altimeter_api_service.update_task(task.remote_id, task_data)
        elif task.related_altimeter_task_id:
            # Fallback for legacy field
             await altimeter_api_service.update_task(task.related_altimeter_task_id, task_data)
             task.remote_id = task.related_altimeter_task_id
        else:
            new_remote_task = await altimeter_api_service.create_task(task_data)
            task.remote_id = str(new_remote_task.get("id"))
            task.related_altimeter_task_id = str(new_remote_task.get("id"))

        task.last_synced_at = datetime.now(timezone.utc)
        task.sync_status = 'synced'

    async def _sync_pull_task(self, item: SyncQueue, db: Session):
        """Pulls a remote task from Altimeter with conflict detection."""
        task = db.query(Task).filter(Task.task_id == item.entity_id).first()
        if not task:
            return

        remote_id = task.remote_id or task.related_altimeter_task_id
        if not remote_id:
            return

        remote_task = await altimeter_api_service.get_task(remote_id)
        if not remote_task:
            return

        # CONFLICT DETECTION
        local_updated = task.updated_at if task.updated_at else task.created_at
        if local_updated.tzinfo is None:
            local_updated = local_updated.replace(tzinfo=timezone.utc)

        remote_updated_str = remote_task.get("updated_at")
        last_sync = task.last_synced_at
        if last_sync and last_sync.tzinfo is None:
            last_sync = last_sync.replace(tzinfo=timezone.utc)

        if remote_updated_str:
            remote_updated = datetime.fromisoformat(remote_updated_str.replace('Z', '+00:00'))

            # Check if both changed since last sync
            if last_sync and local_updated > last_sync and remote_updated > last_sync:
                # CONFLICT: Both sides changed
                time_delta = abs((local_updated - remote_updated).total_seconds())

                if time_delta < 300:  # Within 5 minutes
                    # Create conflict record
                    conflict = SyncConflict(
                        entity_type='task',
                        entity_id=task.task_id,
                        local_version={
                            "title": task.title,
                            "description": task.description,
                            "status": task.status,
                            "priority": task.priority,
                            "due_date": task.due_date.isoformat() if task.due_date else None,
                            "updated_at": local_updated.isoformat()
                        },
                        remote_version={
                            "title": remote_task.get("title"),
                            "description": remote_task.get("description"),
                            "status": remote_task.get("status"),
                            "priority": remote_task.get("priority"),
                            "due_date": remote_task.get("due_date"),
                            "updated_at": remote_updated.isoformat()
                        },
                        status='unresolved'
                    )
                    db.add(conflict)

                    # Mark sync item as conflict
                    item.status = 'conflict'
                    task.sync_status = 'conflict'

                    logger.warning(f"Conflict detected for task {task.task_id}")

                    # Notify UI
                    if self._ws_manager:
                        await self._ws_manager.broadcast_sync_status('task', task.task_id, 'conflict')

                    return  # Don't auto-merge

        # No conflict, safe to merge
        task.title = remote_task.get("title", task.title)
        task.description = remote_task.get("description", task.description)
        task.status = remote_task.get("status", task.status)
        task.priority = remote_task.get("priority", task.priority)

        if remote_task.get("due_date"):
            task.due_date = datetime.fromisoformat(remote_task["due_date"])

        task.last_synced_at = datetime.now(timezone.utc)
        task.sync_status = 'synced'

    def _log_history(self, db: Session, item: SyncQueue, status: str, details: str = None):
        log = SyncActivityLog(
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            direction=item.direction,
            status=status,
            details=details
        )
        db.add(log)

    def enqueue_task(self, db: Session, task_id: int, direction: str):
        """Helper to enqueue a task for sync."""
        existing = db.query(SyncQueue).filter(
            SyncQueue.entity_type == 'task',
            SyncQueue.entity_id == task_id,
            SyncQueue.direction == direction,
            or_(SyncQueue.status == 'pending', SyncQueue.status == 'retry')
        ).first()

        if existing:
            return existing

        item = SyncQueue(
            entity_type='task',
            entity_id=task_id,
            direction=direction,
            status='pending'
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

altimeter_sync_service = AltimeterSyncService()
