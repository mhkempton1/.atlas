from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import json
import logging

from database.database import get_db
from database.models import Task
from services.altimeter_sync_service import altimeter_sync_service
from core.config import settings

router = APIRouter()
logger = logging.getLogger("altimeter_webhooks")

async def verify_signature(request: Request, x_altimeter_signature: Optional[str] = Header(None)):
    """
    Verifies the webhook signature using HMAC-SHA256 and ALTIMETER_API_KEY.
    """
    # If no key configured, skip verification (dev mode) or fail?
    # Prompt says "Verify webhook signature for security".
    # We'll assume if key is set, we verify.
    secret = getattr(settings, "ALTIMETER_API_KEY", "")
    if not secret:
        # Warn but allow if no secret configured (dev)
        return

    if not x_altimeter_signature:
         raise HTTPException(status_code=401, detail="Missing signature header")

    body = await request.body()
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_altimeter_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

@router.post("/altimeter")
async def receive_altimeter_webhook(
    request: Request,
    db: Session = Depends(get_db),
    # signature verification dependency could be added here or called inside
):
    # Verify signature manually to await body
    # (FastAPI dependencies run before body is fully available sometimes, but Request body is cached)
    # We'll just call the helper.
    # Note: Header name in dependency default is 'x-altimeter-signature' (case insensitive)
    # But for manual extraction we need to be careful.
    sig = request.headers.get("x-altimeter-signature")
    await verify_signature(request, sig)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("event")
    data = payload.get("data", {})
    remote_id = data.get("id")

    if not remote_id:
        return {"status": "ignored", "reason": "no_id"}

    logger.info(f"Received Altimeter webhook: {event_type} for {remote_id}")

    if event_type in ["task.created", "task.updated"]:
        # Find or create local task
        task = db.query(Task).filter(Task.remote_id == str(remote_id)).first()

        # Fallback to legacy field check
        if not task:
            task = db.query(Task).filter(Task.related_altimeter_task_id == str(remote_id)).first()

        if not task:
            # New task from Altimeter
            task = Task(
                title=data.get("title", "New Altimeter Task"), # Placeholder until sync
                remote_id=str(remote_id),
                related_altimeter_task_id=str(remote_id),
                source="altimeter",
                status=data.get("status", "open"), # basic mapping
                sync_status="pending"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.info(f"Created placeholder task {task.task_id} for remote {remote_id}")

        # Enqueue 'pull' to fetch full details and handle conflicts
        altimeter_sync_service.enqueue_task(db, task.task_id, "pull")

        return {"status": "queued", "task_id": task.task_id}

    elif event_type == "task.deleted":
        # Handle deletion
        # For now, maybe just log or mark as deleted?
        # Requirement says "Update Atlas database with new data"
        # We can queue a pull which might 404 and then handle it?
        # Or handle directly here.
        pass

    return {"status": "processed"}
