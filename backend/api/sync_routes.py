from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database.database import get_db
from database.models import SyncQueue, SyncActivityLog, Task, SyncConflict
from services.altimeter_sync_service import altimeter_sync_service
from services.altimeter_api_service import altimeter_api_service

router = APIRouter()
logger = logging.getLogger("sync_routes")

@router.get("/status")
async def get_sync_status(db: Session = Depends(get_db)):
    """
    Get overview of sync status.
    """
    pending = db.query(SyncQueue).filter(SyncQueue.status == 'pending').count()
    failed = db.query(SyncQueue).filter(SyncQueue.status == 'failed').count()
    recent_errors = db.query(SyncActivityLog).filter(SyncActivityLog.status == 'failed').order_by(SyncActivityLog.timestamp.desc()).limit(5).all()

    return {
        "queue": {
            "pending": pending,
            "failed": failed
        },
        "recent_errors": [
            {
                "id": e.id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "error": e.details,
                "time": e.timestamp
            } for e in recent_errors
        ],
        "worker_running": altimeter_sync_service.is_running
    }

# Endpoint to start/stop worker manually (for debugging)
@router.post("/worker/{action}")
async def control_worker(action: str):
    if action == "start":
        import asyncio
        asyncio.create_task(altimeter_sync_service.start_worker())
        return {"status": "started"}
    elif action == "stop":
        altimeter_sync_service.stop_worker()
        return {"status": "stopped"}
    return {"status": "unknown action"}

# Conflict Resolution Endpoints

@router.get("/conflicts/task/{task_id}")
async def get_conflict_for_task(task_id: int, db: Session = Depends(get_db)):
    """
    Get unresolved conflict details for a specific task.
    """
    conflict = db.query(SyncConflict).filter(
        SyncConflict.entity_id == task_id,
        SyncConflict.entity_type == 'task',
        SyncConflict.status == 'unresolved'
    ).first()

    if not conflict:
        raise HTTPException(status_code=404, detail="No unresolved conflict found for this task")

    return conflict

@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    resolution: Dict[str, str] = Body(...),  # {"choice": "local" or "remote"}
    db: Session = Depends(get_db)
):
    """
    Resolve a sync conflict by choosing local or remote version.
    """
    conflict = db.query(SyncConflict).filter(SyncConflict.id == conflict_id).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    task = db.query(Task).filter(Task.task_id == conflict.entity_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    choice = resolution.get("choice")

    if choice == "local":
        # Keep local, push to remote
        altimeter_sync_service.enqueue_task(db, task.task_id, "push")
        conflict.status = "resolved_local"
    elif choice == "remote":
        # Accept remote, update local
        remote_data = conflict.remote_version
        task.title = remote_data.get("title", task.title)
        task.description = remote_data.get("description", task.description)
        task.status = remote_data.get("status", task.status)
        task.priority = remote_data.get("priority", task.priority)
        task.sync_status = "synced"
        conflict.status = "resolved_remote"
    else:
        raise HTTPException(status_code=400, detail="Invalid choice")

    conflict.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "resolved", "choice": choice}
