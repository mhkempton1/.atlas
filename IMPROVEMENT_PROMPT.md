# ATLAS IMPROVEMENT & OPTIMIZATION PROMPT

## Current State Analysis

Based on `backend/core/app.py` and `backend/api/routes.py`, Atlas has:
- ✅ FastAPI backend with basic health check
- ✅ CORS configured for frontend (4202/4204)
- ✅ API router with draft agent and email sending
- ✅ Services: Gmail, AI, Altimeter, Document Control, Knowledge, OneDrive, Scheduler
- ⚠️ Health check returns generic status (no real monitoring)
- ⚠️ No database implementation (critical missing piece!)
- ⚠️ No email sync implementation (only send exists)
- ⚠️ No task/calendar management API endpoints

---

## PRIORITY IMPROVEMENTS (In Order of Impact)

### 🔴 CRITICAL: Implement Core Database Layer

#### 1. Create Database Schema (SQLAlchemy Models)

**Current Gap**: No database! Atlas needs to store emails, tasks, contacts, calendar events.

**What to Build**:

```python
# backend/database/models.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Email(Base):
    __tablename__ = 'emails'

    email_id = Column(Integer, primary_key=True)
    message_id = Column(String, unique=True, nullable=False, index=True)
    thread_id = Column(String, index=True)
    gmail_id = Column(String, unique=True, index=True)

    # Addresses
    from_address = Column(String, index=True)
    from_name = Column(String)
    to_addresses = Column(JSON)  # Array of recipients
    cc_addresses = Column(JSON)
    bcc_addresses = Column(JSON)

    # Content - NEVER TRUNCATE!
    subject = Column(Text)
    body_text = Column(Text)  # FULL TEXT - NEVER TRUNCATE
    body_html = Column(Text)  # FULL HTML - NEVER TRUNCATE
    snippet = Column(String(200))  # 200 char preview only

    # Metadata
    date_received = Column(DateTime, index=True)
    date_sent = Column(DateTime)
    labels = Column(JSON)  # Gmail labels
    category = Column(String, index=True)  # work/personal/urgent/spam
    importance = Column(String)  # high/medium/low

    # Attachments
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)

    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_starred = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)

    # Integration
    project_id = Column(String, index=True)  # Link to Altimeter
    contact_id = Column(Integer, ForeignKey('contacts.contact_id'))

    # Preservation
    raw_eml = Column(Text)  # Full EML for archival
    vector_embedding = Column(Text)  # For ChromaDB reference

    # Audit
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)
    synced_at = Column(DateTime)

    # Relationships
    contact = relationship("Contact", back_populates="emails")
    attachments = relationship("EmailAttachment", back_populates="email")

    __table_args__ = (
        Index('idx_email_project_date', 'project_id', 'date_received'),
        Index('idx_email_category_date', 'category', 'date_received'),
    )


class EmailAttachment(Base):
    __tablename__ = 'email_attachments'

    attachment_id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey('emails.email_id'), index=True)
    filename = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    file_path = Column(String)  # Local storage path
    file_hash = Column(String)  # SHA256 for deduplication
    gmail_attachment_id = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    email = relationship("Email", back_populates="attachments")


class Contact(Base):
    __tablename__ = 'contacts'

    contact_id = Column(Integer, primary_key=True)
    name = Column(String)
    email_address = Column(String, unique=True, index=True)
    phone = Column(String)
    company = Column(String)
    role = Column(String)
    category = Column(String, index=True)  # work/personal/vendor/customer

    # Altimeter Integration
    altimeter_customer_id = Column(Integer)
    altimeter_vendor_id = Column(Integer)

    # Stats
    last_contact_date = Column(DateTime)
    email_count = Column(Integer, default=0)
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)

    # Relationships
    emails = relationship("Email", back_populates="contact")


class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, index=True)  # todo/in_progress/done/blocked
    priority = Column(String, index=True)  # high/medium/low
    category = Column(String)  # work/personal/home

    # Integration
    project_id = Column(String, index=True)  # Altimeter project
    email_id = Column(Integer, ForeignKey('emails.email_id'))

    # Scheduling
    due_date = Column(DateTime, index=True)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    # Hierarchy
    parent_task_id = Column(Integer, ForeignKey('tasks.task_id'))

    # Source tracking
    created_from = Column(String)  # manual/email/ai_suggested

    # Audit
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)

    __table_args__ = (
        Index('idx_task_status_due', 'status', 'due_date'),
    )


class CalendarEvent(Base):
    __tablename__ = 'calendar_events'

    event_id = Column(Integer, primary_key=True)
    google_event_id = Column(String, unique=True, index=True)
    calendar_id = Column(String)  # work/personal

    # Event Details
    title = Column(String)
    description = Column(Text)
    location = Column(String)

    # Timing
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime)
    all_day = Column(Boolean, default=False)

    # Participants
    attendees = Column(JSON)  # Array of email addresses
    organizer = Column(String)

    # Status
    status = Column(String)  # confirmed/tentative/cancelled

    # Integration
    project_id = Column(String, index=True)  # Altimeter project

    # Audit
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)
    synced_at = Column(DateTime)


class Draft(Base):
    __tablename__ = 'drafts'

    draft_id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey('emails.email_id'))  # Original if reply

    # Recipient Info
    recipient = Column(String)
    cc = Column(String)
    bcc = Column(String)
    subject = Column(String)

    # Content
    body_text = Column(Text)
    body_html = Column(Text)

    # AI Metadata
    generated_by = Column(String)  # ai/user
    ai_model = Column(String)  # gemini-2.0-flash
    generation_prompt = Column(Text)

    # Status
    status = Column(String)  # draft/scheduled/sent
    scheduled_time = Column(DateTime)
    sent_time = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime)
```

**Database Initialization**:

```python
# backend/database/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# SQLite database
DATABASE_URL = f"sqlite:///{settings.DATA_DIR}/databases/atlas.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
from database.models import Base
Base.metadata.create_all(bind=engine)
```

**Update `core/app.py`**:

```python
# core/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

# Initialize database
from database.database import engine, Base
from database import models
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Atlas Personal AI Assistant Backend"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "status": "online",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check():
    # Test database connection
    try:
        from database.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "altimeter": check_altimeter_connection(),
        "gmail": check_gmail_connection()
    }

from api.routes import router as api_router
app.include_router(api_router, prefix=settings.API_PREFIX)
```

---

#### 2. Implement Gmail Sync (CRITICAL - Currently Only Send Exists)

**Current Gap**: Can send emails but cannot sync/read from Gmail.

**What to Build**:

```python
# backend/services/gmail_service.py (COMPLETE REWRITE)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import os
from datetime import datetime
from database.database import get_db
from database.models import Email, EmailAttachment, Contact

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """OAuth 2.0 authentication with Google"""
        creds = None

        # Token file stores refresh token
        token_path = 'config/gmail_token.json'
        creds_path = 'config/gmail_credentials.json'

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def sync_emails(self, last_sync_timestamp=None):
        """Sync emails from Gmail - NEVER TRUNCATE BODIES"""

        db = next(get_db())

        # Build query
        if last_sync_timestamp:
            # Only fetch emails after last sync
            query = f"after:{int(last_sync_timestamp.timestamp())}"
        else:
            # Initial sync - last 30 days
            query = "newer_than:30d"

        try:
            # Fetch message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Batch size
            ).execute()

            messages = results.get('messages', [])

            for msg_ref in messages:
                # Fetch full message
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='full'
                ).execute()

                # Parse and store
                self._store_email(message, db)

            db.commit()

            return {
                'synced': len(messages),
                'timestamp': datetime.now()
            }

        except Exception as e:
            db.rollback()
            raise Exception(f"Email sync failed: {str(e)}")

    def _store_email(self, message, db):
        """Parse Gmail message and store in database"""

        # Check if already exists
        gmail_id = message['id']
        existing = db.query(Email).filter_by(gmail_id=gmail_id).first()
        if existing:
            return  # Skip duplicates

        # Parse headers
        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Extract body
        body_text, body_html = self._extract_body(message['payload'])

        # Create email record
        email = Email(
            message_id=headers.get('Message-ID'),
            thread_id=message['threadId'],
            gmail_id=gmail_id,
            from_address=headers.get('From'),
            to_addresses=[headers.get('To')],
            subject=headers.get('Subject'),
            body_text=body_text,  # FULL BODY - NEVER TRUNCATE
            body_html=body_html,  # FULL HTML - NEVER TRUNCATE
            snippet=message.get('snippet', '')[:200],  # Preview only
            date_received=self._parse_date(headers.get('Date')),
            labels=message.get('labelIds', []),
            is_read='UNREAD' not in message.get('labelIds', []),
            synced_at=datetime.now()
        )

        db.add(email)
        db.flush()  # Get email_id

        # Download attachments
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part.get('filename'):
                    self._download_attachment(part, email.email_id, gmail_id, db)

        # Auto-categorize with AI
        from services.ai_service import categorize_email
        email.category = categorize_email(email.subject, email.body_text)

        # Link to Altimeter project if work email
        if email.category == 'work':
            from services.altimeter_service import link_email_to_project
            email.project_id = link_email_to_project(email)

    def _extract_body(self, payload):
        """Extract email body - handles multipart MIME"""
        body_text = ""
        body_html = ""

        if 'body' in payload and payload['body'].get('data'):
            # Simple message
            data = payload['body']['data']
            decoded = base64.urlsafe_b64decode(data).decode('utf-8')

            if payload.get('mimeType') == 'text/html':
                body_html = decoded
            else:
                body_text = decoded

        elif 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif part['mimeType'] == 'text/html' and part['body'].get('data'):
                    body_html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

        return body_text, body_html

    def _download_attachment(self, part, email_id, gmail_id, db):
        """Download email attachment"""

        attachment_id = part['body'].get('attachmentId')
        if not attachment_id:
            return

        # Download from Gmail
        attachment = self.service.users().messages().attachments().get(
            userId='me',
            messageId=gmail_id,
            id=attachment_id
        ).execute()

        # Save to disk
        file_data = base64.urlsafe_b64decode(attachment['data'])
        filename = part['filename']
        file_path = f"data/files/attachments/{email_id}/{filename}"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Store metadata
        attachment_record = EmailAttachment(
            email_id=email_id,
            filename=filename,
            file_size=len(file_data),
            mime_type=part['mimeType'],
            file_path=file_path,
            gmail_attachment_id=attachment_id
        )
        db.add(attachment_record)

    def send_email(self, recipient, subject, body):
        """Send email via Gmail"""
        # Existing implementation...
        pass

gmail_service = GmailService()
```

**Add Sync Endpoint**:

```python
# backend/api/routes.py

@router.post("/email/sync")
async def sync_gmail():
    """Trigger email sync from Gmail"""

    from services.gmail_service import gmail_service
    from database.database import get_db
    from database.models import Email

    db = next(get_db())

    # Get last sync timestamp
    last_email = db.query(Email).order_by(Email.synced_at.desc()).first()
    last_sync = last_email.synced_at if last_email else None

    # Sync
    result = gmail_service.sync_emails(last_sync)

    return result
```

---

#### 3. Implement Background Email Sync Scheduler

**What to Build**:

```python
# backend/services/scheduler_service.py (ENHANCE EXISTING)

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

scheduler = BackgroundScheduler()

def sync_emails_job():
    """Background job to sync emails every 5 minutes"""
    from services.gmail_service import gmail_service
    from database.database import get_db
    from database.models import Email

    db = next(get_db())

    # Get last sync
    last_email = db.query(Email).order_by(Email.synced_at.desc()).first()
    last_sync = last_email.synced_at if last_email else None

    # Sync
    try:
        result = gmail_service.sync_emails(last_sync)
        print(f"[{datetime.now()}] Email sync: {result['synced']} new emails")

        # After sync, extract tasks from new emails
        extract_tasks_from_new_emails(db)

    except Exception as e:
        print(f"Email sync failed: {e}")

def extract_tasks_from_new_emails(db):
    """AI task extraction from newly synced emails"""
    from services.ai_service import extract_tasks_from_email
    from database.models import Email, Task

    # Get unprocessed emails
    new_emails = db.query(Email).filter(
        Email.synced_at > datetime.now() - timedelta(minutes=10),
        Email.category == 'work'
    ).all()

    for email in new_emails:
        # AI extraction
        tasks = extract_tasks_from_email(email.subject, email.body_text)

        for task_data in tasks:
            task = Task(
                title=task_data['title'],
                description=task_data['description'],
                priority=task_data['priority'],
                due_date=task_data.get('due_date'),
                project_id=email.project_id,
                email_id=email.email_id,
                created_from='email',
                status='todo'
            )
            db.add(task)

    db.commit()

# Schedule jobs
scheduler.add_job(sync_emails_job, 'interval', minutes=5, id='email_sync')
scheduler.start()
```

**Add to `core/app.py`**:

```python
from services.scheduler_service import scheduler

@app.on_event("startup")
def startup_event():
    print("Atlas starting up...")
    print("Background email sync enabled (every 5 minutes)")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
```

---

### 🟠 HIGH PRIORITY: Complete API Endpoints

#### 4. Add Email API Endpoints

```python
# backend/api/email_routes.py (NEW FILE)

from fastapi import APIRouter, Depends, HTTPException, Query
from database.database import get_db
from database.models import Email
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter()

@router.get("/email/list")
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

@router.get("/email/{email_id}")
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get single email with full body"""

    email = db.query(Email).filter(Email.email_id == email_id).first()

    if not email:
        raise HTTPException(404, "Email not found")

    # Mark as read
    if not email.is_read:
        email.is_read = True
        db.commit()

    return email

@router.post("/email/{email_id}/star")
async def toggle_star(email_id: int, db: Session = Depends(get_db)):
    """Star/unstar email"""

    email = db.query(Email).filter(Email.email_id == email_id).first()

    if not email:
        raise HTTPException(404, "Email not found")

    email.is_starred = not email.is_starred
    db.commit()

    return {"starred": email.is_starred}

# Include in main routes.py
from api.email_routes import router as email_router
router.include_router(email_router, prefix="/email", tags=["Email"])
```

---

#### 5. Add Task API Endpoints

```python
# backend/api/task_routes.py (NEW FILE)

from fastapi import APIRouter, Depends
from database.database import get_db
from database.models import Task
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[str] = None
    project_id: Optional[str] = None

@router.get("/tasks/list")
async def get_tasks(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tasks with filtering"""

    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)
    if project_id:
        query = query.filter(Task.project_id == project_id)

    tasks = query.order_by(Task.due_date.asc()).all()

    return tasks

@router.post("/tasks/create")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create task manually"""

    new_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        project_id=task.project_id,
        created_from='manual',
        status='todo'
    )

    db.add(new_task)
    db.commit()

    return new_task

@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark task as complete"""

    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(404, "Task not found")

    task.status = 'done'
    task.completed_at = datetime.now()
    db.commit()

    return task
```

---

### 🟡 MEDIUM PRIORITY: AI Enhancements

#### 6. Enhance Draft Agent with Project Context

```python
# backend/agents/draft_agent.py (ENHANCE EXISTING)

async def process(self, context):
    """Generate draft with project context from Altimeter"""

    # Get project context if email is work-related
    project_context = None
    if context.get('project_id'):
        from services.altimeter_service import get_project_context
        project_context = get_project_context(context['project_id'])

    # Build enhanced prompt
    prompt = f"""
    You are drafting an email response.

    Original Email:
    From: {context['sender']}
    Subject: {context['subject']}
    Body: {context['body']}

    {"Project Context: " + str(project_context) if project_context else ""}

    Instructions: {context['instructions']}

    Generate a professional email response.
    """

    # Call Gemini
    response = self.gemini_client.generate_content(prompt)

    return {
        "draft_text": response.text,
        "status": "success",
        "model": "gemini-2.0-flash",
        "context_used": project_context
    }
```

---

## IMPROVEMENT ROADMAP

### Week 1: Core Database & Email Sync (CRITICAL)
- [ ] Day 1-2: Create database schema (Task #1)
- [ ] Day 3-4: Implement Gmail sync (Task #2)
- [ ] Day 5: Test email sync and storage

### Week 2: Background Sync & API Endpoints
- [ ] Day 1: Add background scheduler (Task #3)
- [ ] Day 2-3: Email API endpoints (Task #4)
- [ ] Day 4-5: Task API endpoints (Task #5)

### Week 3: AI Enhancements & Calendar
- [ ] Day 1-2: Enhance draft agent with context (Task #6)
- [ ] Day 3-4: Implement calendar sync
- [ ] Day 5: Testing and validation

---

## VALIDATION CHECKLIST

After improvements, verify:

- [ ] Database created at `data/databases/atlas.db`
- [ ] Email sync works (fetch 50+ emails from Gmail)
- [ ] Email bodies stored in full (NEVER truncated)
- [ ] Emails auto-link to Altimeter projects (test with work emails)
- [ ] Background sync runs every 5 minutes
- [ ] Tasks extract from emails automatically
- [ ] Draft generation includes project context
- [ ] Health check shows real database/Gmail status
- [ ] API endpoints: `/email/list`, `/email/{id}`, `/tasks/list`, `/tasks/create`
- [ ] No errors in console during sync

---

## EXPECTED OUTCOMES

**Functionality**:
- Atlas can READ emails (not just send)
- Emails stored locally for offline access
- Automatic project linking (work emails → Altimeter)
- Automatic task extraction from emails

**Performance**:
- Background sync (no manual triggers)
- Fast email search (database queries)
- Offline functionality (local database)

**AI Intelligence**:
- Draft responses with project context
- Categorization (work/personal/urgent)
- Task extraction with priority detection

**Integration**:
- Seamless Altimeter project linking
- Shared contact database
- Email correspondence tracked in Altimeter

---

**Start with Week 1 (Database & Email Sync) - Atlas is incomplete without email storage!**
