from fastapi import APIRouter, Depends, HTTPException, Query
from database.database import get_db
from database.models import Email
from sqlalchemy.orm import Session
from typing import Optional, List

router = APIRouter()

@router.get("/labels")
async def get_labels():
    """Get available Gmail labels/folders"""
    from services.google_service import google_service
    return google_service.get_labels()

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
    gmail_id: Optional[str] = None
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

    from services.google_service import google_service
    from database.models import Email as EmailModel
    from database.database import SessionLocal

    db = SessionLocal()
    try:
        # Get last sync timestamp
        last_email = db.query(EmailModel).order_by(EmailModel.synced_at.desc()).first()
        last_sync = last_email.synced_at if last_email else None

        # Sync
        result = google_service.sync_emails(last_sync)

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
    """
    from services.google_service import google_service
    from services.altimeter_service import altimeter_service
    from agents.task_agent import task_agent
    from agents.calendar_agent import calendar_agent
    from database.models import Task, CalendarEvent
    
    # 1. Fetch from Google
    sync_result = google_service.sync_emails()
    
    # 2. Get latest emails for processing
    emails = db.query(Email).order_by(Email.date_received.desc()).limit(limit).all()
    
    tasks_res = []
    events_res = []
    
    for email in emails:
        # Get context from Altimeter
        context = altimeter_service.get_context_for_email(email.from_address, email.subject)
        
        # Agentic Extraction
        agent_context = {
            "subject": email.subject,
            "sender": email.from_address,
            "body": email.body_text or "",
            "message_id": email.message_id
        }
        
        # Check for Proposal FIRST to override agent if needed, or pass as hint
        if context.get("is_proposal"):
             agent_context["instructions"] = "This appears to be a Request for Proposal (RFP). Create a high priority task to review and bid."

        # 1. Tasks
        task_out = await task_agent.process(agent_context)
        if task_out.get("status") == "success":
            for t_data in task_out["data"].get("tasks", []):
                # Force proposal formatting if detected
                if context.get("is_proposal"):
                    t_data["title"] = f"PROPOSAL: {t_data['title']}"
                    t_data["priority"] = "high"
                    
                new_task = Task(
                    title=t_data["title"],
                    description=t_data["description"],
                    priority=t_data["priority"].lower(),
                    due_date=datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
                    project_id=context.get("project", {}).get("number") if context.get("project") else None,
                    email_id=email.email_id,
                    created_from="email"
                )
                db.add(new_task)
                db.flush()
                tasks_res.append(TaskResult(
                    task_id=new_task.task_id,
                    title=new_task.title,
                    project_id=new_task.project_id,
                    priority=new_task.priority,
                    context_precursor=context.get("file_context", ""),
                    type="proposal" if context.get("is_proposal") else "task"
                ))
        
        # 2. Events
        event_out = await calendar_agent.process(agent_context)
        if event_out.get("status") == "success" and event_out["data"].get("is_event"):
            e_data = event_out["data"]["event"]
            new_event = CalendarEvent(
                title=e_data["title"],
                description=e_data["description"],
                location=e_data.get("location"),
                start_time=datetime.fromisoformat(e_data["start_time"]) if e_data.get("start_time") else None,
                end_time=datetime.fromisoformat(e_data["end_time"]) if e_data.get("end_time") else None,
                status="confirmed",
                project_id=context.get("project", {}).get("number") if context.get("project") else None
            )
            db.add(new_event)
            db.flush()
            events_res.append(EventResult(
                event_id=new_event.event_id,
                title=new_event.title,
                start_time=new_event.start_time.isoformat() if new_event.start_time else None
            ))

    db.commit()

    return ScanResult(
        emails_found=len(emails),
        tasks_created=tasks_res,
        events_created=events_res
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
    if not email.gmail_id:
        raise HTTPException(status_code=400, detail="Email has no Gmail ID for reply")

    result = google_service.reply_to_email(email.gmail_id, request.body, request.reply_all)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Reply failed'))

    return result

@router.post("/{email_id}/forward")
async def forward_email(email_id: int, request: ForwardRequest, db: Session = Depends(get_db)):
    """Forward an email via Gmail API"""
    from services.google_service import google_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if not email.gmail_id:
        raise HTTPException(status_code=400, detail="Email has no Gmail ID for forward")

    result = google_service.forward_email(email.gmail_id, request.to_address, request.note)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Forward failed'))

    return result

@router.delete("/{email_id}")
async def delete_email(email_id: int, db: Session = Depends(get_db)):
    """Trash email in Gmail and remove from local DB"""
    from services.google_service import google_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Trash in Gmail
    if email.gmail_id:
        result = google_service.trash_email(email.gmail_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Gmail trash failed'))

    # Remove from local DB
    db.delete(email)
    db.commit()

    return {"success": True, "message": "Email deleted"}

@router.post("/{email_id}/archive")
async def archive_email(email_id: int, db: Session = Depends(get_db)):
    """Archive email in Gmail (remove from INBOX label)"""
    from services.google_service import google_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if email.gmail_id:
        result = google_service.archive_email(email.gmail_id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Archive failed'))

    # Mark as archived locally (using category field)
    email.category = 'archived'
    db.commit()

    return {"success": True, "message": "Email archived"}

@router.post("/{email_id}/unread")
async def mark_unread(email_id: int, db: Session = Depends(get_db)):
    """Mark email as unread in Gmail and locally"""
    from services.google_service import google_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if email.gmail_id:
        google_service.mark_unread(email.gmail_id)

    email.is_read = False
    db.commit()

    return {"success": True, "message": "Marked as unread"}

@router.post("/{email_id}/move")
async def move_email(email_id: int, request: MoveRequest, db: Session = Depends(get_db)):
    """Move email to a Gmail label/folder"""
    from services.google_service import google_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if not email.gmail_id:
        raise HTTPException(status_code=400, detail="Email has no Gmail ID")

    result = google_service.move_to_label(email.gmail_id, request.label_name)
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

