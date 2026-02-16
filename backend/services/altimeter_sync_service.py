import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import SessionLocal
from database.models import Task, SyncQueue, SyncActivityLog
from services.altimeter_api_service import altimeter_api_service

# Configure logging
logger = logging.getLogger("altimeter_sync")
logger.setLevel(logging.INFO)

class AltimeterSyncService:
    def __init__(self):
        self.is_running = False
        self._ws_manager = None # To be injected later

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

        # Notify UI (Phase 3 placeholder)
        if self._ws_manager:
            await self._ws_manager.broadcast_sync_status(item.entity_type, item.entity_id, "syncing")

        try:
            if item.entity_type == 'task':
                if item.direction == 'push':
                    await self._sync_push_task(item, db)
                elif item.direction == 'pull':
                    await self._sync_pull_task(item, db)

            item.status = 'synced'
            item.error_message = None
            # Log success
            self._log_history(db, item, "success")
            db.commit()

            # Notify UI
            if self._ws_manager:
                await self._ws_manager.broadcast_sync_status(item.entity_type, item.entity_id, "synced")

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
            # If task deleted locally, we might want to delete remote.
            # But usually 'push' happens on update/create.
            # If it was a 'delete' push, we should have marked it in metadata or checked task existence.
            # Assuming 'delete' is handled separately or by checking 'deleted_at' (if we had soft deletes).
            # If hard delete, we can't get task details.
            # So delete should be a different queue item or store payload.
            # For now, simplistic: if not found, ignore or assume deleted.
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
        # No db.commit() here, done in caller

    async def _sync_pull_task(self, item: SyncQueue, db: Session):
        """Pulls a remote task from Altimeter."""
        task = db.query(Task).filter(Task.task_id == item.entity_id).first()
        if not task:
            return

        remote_id = task.remote_id or task.related_altimeter_task_id
        if not remote_id:
            # Can't pull without remote ID
            return

        remote_task = await altimeter_api_service.get_task(remote_id)
        if not remote_task:
            return

        # Simple update for now
        # Ideally check conflict

        task.title = remote_task.get("title", task.title)
        task.description = remote_task.get("description", task.description)
        task.status = remote_task.get("status", task.status)
        # Map priority/status if values differ

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
