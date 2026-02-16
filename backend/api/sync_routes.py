from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List, Dict, Any, Optional
import json
import logging
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import SyncQueue, SyncActivityLog, Task
from services.altimeter_sync_service import altimeter_sync_service
from services.altimeter_api_service import altimeter_api_service

router = APIRouter()
logger = logging.getLogger("sync_routes")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        msg_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(msg_str)
            except Exception:
                pass

    async def broadcast_sync_status(self, entity_type: str, entity_id: int, status: str):
        message = {
            "type": "sync_update",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status
        }
        await self.broadcast(message)

manager = ConnectionManager()

# Inject manager into sync service
altimeter_sync_service.set_ws_manager(manager)

@router.websocket("/ws/sync-status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

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

@router.get("/conflict/task/{task_id}")
async def get_conflict_details(task_id: int, db: Session = Depends(get_db)):
    """
    Get details of a conflict, including local and remote versions.
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Local version
    local_version = {
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None
    }

    # Remote version (fetch from Altimeter)
    remote_id = task.remote_id or task.related_altimeter_task_id
    if not remote_id:
         raise HTTPException(status_code=400, detail="No remote ID, cannot resolve conflict")

    remote_task = await altimeter_api_service.get_task(remote_id)
    if not remote_task:
        raise HTTPException(status_code=404, detail="Remote task not found")

    return {
        "local": local_version,
        "remote": remote_task
    }

from pydantic import BaseModel
class ResolveConflictRequest(BaseModel):
    strategy: str # local, remote

@router.post("/resolve/task/{task_id}")
async def resolve_conflict(task_id: int, request: ResolveConflictRequest, db: Session = Depends(get_db)):
    """
    Resolve a conflict.
    strategy: "local" (push) or "remote" (pull)
    """
    strategy = request.strategy
    if strategy not in ["local", "remote"]:
        raise HTTPException(status_code=400, detail="Invalid strategy")

    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if strategy == "local":
        # Push local to remote
        task.sync_status = "pending"
        db.commit()
        altimeter_sync_service.enqueue_task(db, task.task_id, "push")

    elif strategy == "remote":
        # Pull remote to local
        task.sync_status = "pending"
        db.commit()
        altimeter_sync_service.enqueue_task(db, task.task_id, "pull")

    return {"status": "resolution_queued"}
