from fastapi import APIRouter, Depends, HTTPException, Query
from database.database import get_db
from database.models import Email
from sqlalchemy.orm import Session
from typing import Optional, List

router = APIRouter()

@router.get("/labels")
async def get_labels():
    """Get available Gmail labels/folders"""
    from services.communication_service import comm_service
    return comm_service.get_labels()

@router.get("/stats")
async def get_email_stats(db: Session = Depends(get_db)):
    """Get email count statistics"""
    total = db.query(Email).count()
    unread = db.query(Email).filter(Email.is_read == False).count()
    return {
        "total_emails": total,
        "unread_emails": unread
    }

@router.get("/list")
async def get_emails(
    category: Optional[str] = None,
    is_read: Optional[bool] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get emails with filtering"""

    query = db.query(Email)

    if category:
        query = query.filter(Email.category == category)
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)
    if project_id:
        query = query.filter(Email.project_id == project_id)

    # Most recent first
    query = query.order_by(Email.date_received.desc())

    # Pagination
    emails = query.offset(offset).limit(limit).all()

    return emails

from pydantic import BaseModel, ConfigDict
from datetime import datetime

class EmailResponse(BaseModel):
    email_id: int
    subject: Optional[str] = None
    from_address: Optional[str] = None
    from_name: Optional[str] = None
    to_addresses: Optional[list] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    date_received: Optional[datetime] = None
    is_read: bool
    is_starred: bool
    remote_id: Optional[str] = None
    provider_type: Optional[str] = "google"
    has_attachments: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class CategoryUpdate(BaseModel):
    category: str

@router.put("/{email_id}/category")
async def update_category(email_id: int, update: CategoryUpdate, db: Session = Depends(get_db)):
    """Update local category for organization"""
    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.category = update.category
    db.commit()

    return {"success": True, "category": email.category}

@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get single email with full body"""

    email = db.query(Email).filter(Email.email_id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Mark as read
    if not email.is_read:
        email.is_read = True
        db.commit()
        db.refresh(email)

    return email

@router.post("/{email_id}/star")
async def toggle_star(email_id: int, db: Session = Depends(get_db)):
    """Star/unstar email"""

    email = db.query(Email).filter(Email.email_id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.is_starred = not email.is_starred
    db.commit()

    return {"starred": email.is_starred}

@router.post("/sync")
async def sync_gmail():
    """Trigger email sync from Gmail"""

    from database.models import Email as EmailModel
    from database.database import SessionLocal

    db = SessionLocal()
    try:
        # Get last sync timestamp
        last_email = db.query(EmailModel).order_by(EmailModel.synced_at.desc()).first()
        last_sync = last_email.synced_at if last_email else None

        # Sync
        from services.communication_service import comm_service
        result = comm_service.sync_emails(last_sync)

        return result
    finally:
        db.close()


class EventResult(BaseModel):
    event_id: int
    title: str
    start_time: Optional[str] = None
    priority: str = "medium"

class TaskResult(BaseModel):
    task_id: int
    title: str
    project_id: Optional[str] = None
    priority: str
    context_precursor: str
    type: str = "task"

class ScanResult(BaseModel):
    emails_found: int
    tasks_created: List[TaskResult]
    events_created: List[EventResult]

@router.post("/scan", response_model=ScanResult)
async def scan_emails(limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    """
    Scan recent emails, identify project context, and generate tasks/events.
    This is the core 'The Lens' bridge logic.

    UPDATED: Uses TaskQueue for asynchronous processing to prevent locking.
    """
    from services.communication_service import comm_service
    from services.data_api import data_api
    
    # 1. Fetch from Provider
    # sync_result = comm_service.sync_emails() 
    
    # 2. Get latest emails for processing
    emails = db.query(Email).order_by(Email.date_received.desc()).limit(limit).all()
    
    for email in emails:
        # Enqueue processing task via Central Data API
        # This prevents locking and allows the "Ingester" (this route) to hand off to "Analyzer" (TaskAgent)
        data_api.add_task(
            type="analyze_email",
            payload={
                "email_id": email.email_id,
                "subject": email.subject,
                "from_address": email.from_address,
                "body_text": email.body_text,
                "remote_id": email.remote_id,
                "provider_type": email.provider_type
            },
            priority=10
        )

    # Return empty results immediately as processing is now async
    return ScanResult(
        emails_found=len(emails),
        tasks_created=[],
        events_created=[]
    )

from pydantic import BaseModel

class ReplyRequest(BaseModel):
    body: str
    reply_all: bool = False

class ForwardRequest(BaseModel):
    to_address: str
    note: Optional[str] = ""

class DraftReplyRequest(BaseModel):
    instructions: Optional[str] = "Draft a professional response."


class MoveRequest(BaseModel):
    label_name: str

@router.post("/{email_id}/reply")
async def reply_to_email(email_id: int, request: ReplyRequest, db: Session = Depends(get_db)):
    """Reply to an email via Gmail API"""
    from services.google_service import google_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if not email.remote_id:
        raise HTTPException(status_code=400, detail="Email has no Remote ID for reply")

    from services.communication_service import comm_service
    result = comm_service.reply_to_email(email.remote_id, request.body, request.reply_all)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Reply failed'))

    return result

@router.post("/{email_id}/forward")
async def forward_email(email_id: int, request: ForwardRequest, db: Session = Depends(get_db)):
    """Forward an email via Gmail API"""
    from services.communication_service import comm_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if not email.remote_id:
        raise HTTPException(status_code=400, detail="Email has no Remote ID for forward")

    result = comm_service.forward_email(email.remote_id, request.to_address, request.note)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Forward failed'))

    return result

@router.delete("/{email_id}")
async def delete_email(email_id: int, db: Session = Depends(get_db)):
    """Trash email in Gmail and remove from local DB"""
    from services.communication_service import comm_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Trash in Provider
    if email.remote_id:
        result = comm_service.trash_email(email.remote_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Trash failed'))

    # Remove from local DB
    db.delete(email)
    db.commit()

    return {"success": True, "message": "Email deleted"}

@router.post("/{email_id}/archive")
async def archive_email(email_id: int, db: Session = Depends(get_db)):
    """Archive email in Gmail (remove from INBOX label)"""
    from services.communication_service import comm_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if email.remote_id:
        result = comm_service.archive_email(email.remote_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Archive failed'))

    # Mark as archived locally (using category field)
    email.category = 'archived'
    db.commit()

    return {"success": True, "message": "Email archived"}

@router.post("/{email_id}/unread")
async def mark_unread(email_id: int, db: Session = Depends(get_db)):
    """Mark email as unread in Gmail and locally"""
    from services.communication_service import comm_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if email.remote_id:
        comm_service.mark_unread(email.remote_id)

    email.is_read = False
    db.commit()

    return {"success": True, "message": "Marked as unread"}

@router.post("/{email_id}/move")
async def move_email(email_id: int, request: MoveRequest, db: Session = Depends(get_db)):
    """Move email to a Gmail label/folder"""
    from services.communication_service import comm_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if not email.remote_id:
        raise HTTPException(status_code=400, detail="Email has no Remote ID")

    result = comm_service.move_to_label(email.remote_id, request.label_name)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Move failed'))

    # Update local category
    email.category = request.label_name.lower()
    db.commit()

    return result



@router.post("/{email_id}/draft-reply")
async def generate_draft_reply(email_id: int, request: DraftReplyRequest, db: Session = Depends(get_db)):
    """Generate an AI draft reply"""
    from agents.draft_agent import draft_agent

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    agent_context = {
        "subject": email.subject,
        "sender": email.from_address,
        "body": email.body_text or "",
        "instructions": request.instructions
    }

    result = await draft_agent.process(agent_context)
    return result

