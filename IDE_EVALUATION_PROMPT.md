# ATLAS SYSTEM EVALUATION & IMPROVEMENT PROMPT FOR IDE LLM

## EVALUATION SUMMARY (2026-01-26)

### SYSTEM STATUS
| Component | Status | Notes |
|-----------|--------|-------|
| Backend Server | ✅ RUNNING | Port 4201, health endpoint responding |
| Frontend Server | ✅ RUNNING | Port 4202, Vite dev server active |
| Database | ✅ HEALTHY | SQLite connection verified |
| Altimeter Integration | ✅ CONNECTED | Health check passing, 11 active projects |
| Gmail Sync | ✅ FUNCTIONAL | 116 emails synced, OAuth working |
| AI Service (Gemini) | ⚠️ PARTIAL | Service initialized but draft agent broken |
| Tests | ❌ FAILING | Import errors preventing test execution |

### CRITICAL ISSUES FOUND

#### Issue 1: Draft Agent - Missing Method (BLOCKING)
**Location**: `backend/services/altimeter_service.py`
**Error**: `'AltimeterService' object has no attribute 'get_context_for_email'`
**Impact**: Draft agent endpoint `/api/v1/agents/draft` returns 500 error

The `DraftAgent` in `backend/agents/draft_agent.py:27` calls:
```python
altimeter_context = altimeter_service.get_context_for_email(sender, subject)
```

But `AltimeterService` only has these methods:
- `parse_email_for_project()`
- `get_project_details()`
- `get_system_status()`
- `generate_response_draft()`

**Required Fix**: Add `get_context_for_email()` method to `AltimeterService`

---

#### Issue 2: Test Suite Import Errors (BLOCKING)
**Location**: `tests/test_atlas_flow.py`
**Error**: `ModuleNotFoundError: No module named 'database'`

Tests import directly from backend modules but Python path is not configured correctly.
Also, test references outdated functions:
- `scan_emails, ScanResult` - these don't exist in current `email_routes.py`
- `ImapService` - replaced by `google_service.py`

**Required Fix**:
1. Update `conftest.py` to add backend to Python path
2. Rewrite tests to use current API structure
3. Remove references to deprecated IMAP service

---

#### Issue 3: Task Agent Not Integrated (INCOMPLETE)
**Location**: `backend/agents/task_agent.py`
**Issue**: TaskAgent exists but is NOT connected to any API route

Current state is just placeholder methods:
- `analyze_task()` - returns hardcoded values
- `prioritize_tasks()` - simple sort only

No endpoint like `/api/v1/tasks/extract` exists to extract tasks from emails.

**Required Fix**:
1. Implement actual AI task extraction using `ai_service`
2. Create task routes in `backend/api/task_routes.py`
3. Wire task extraction into email sync pipeline

---

#### Issue 4: Calendar Agent Missing (NOT IMPLEMENTED)
**Location**: Should be at `backend/agents/calendar_agent.py`
**Issue**: File does not exist

The `IDE_LLM_BUILD_PROMPT.md` specifies a Calendar Agent but it was never created.

**Required Fix**: Create `calendar_agent.py` with:
- `sync_google_calendar()`
- `detect_conflicts()`
- `suggest_meeting_times()`
- `extract_meeting_from_email()`

---

#### Issue 5: Vector Search / ChromaDB Not Implemented (MISSING)
**Location**: Should be at `backend/services/search_service.py`
**Issue**: File does not exist

RAG capabilities documented in architecture are not implemented.

**Required Fix**: Create `search_service.py` with:
- ChromaDB initialization
- `index_email()` - embed and store emails
- `index_file()` - embed documents
- `search_emails()` - semantic search
- `search_files()` - file search

---

### WORKING COMPONENTS (Reference)

These components are functional and can be used as patterns:

1. **GoogleService** (`backend/services/google_service.py`)
   - OAuth authentication working
   - Email sync functional (116 emails)
   - Calendar sync structure exists
   - Attachment download works

2. **Email Routes** (`backend/api/email_routes.py`)
   - `GET /email/list` - ✅ Returns emails with filtering
   - `GET /email/{id}` - ✅ Returns single email
   - `POST /email/{id}/star` - ✅ Toggles star
   - `POST /email/sync` - ✅ Triggers Gmail sync

3. **Document Control** (`backend/services/document_control_service.py`)
   - Draft workflow working
   - State transitions (DRAFT → REVIEW → LOCKED → ARCHIVE)

4. **Knowledge Service** (`backend/services/knowledge_service.py`)
   - Document discovery working
   - Content retrieval functional

5. **Frontend Components**
   - `EmailList.jsx` - Displays inbox
   - `EmailView.jsx` - Shows email details
   - `ComposeDraft.jsx` - Draft composition UI
   - `Dashboard.jsx` - Command center
   - Navigation and routing working

---

## PRIORITY TASKS FOR IDE LLM

### PHASE 1: Fix Critical Blocking Issues

#### Task 1.1: Implement `get_context_for_email()` in AltimeterService
**File**: `C:\Users\mhkem\.atlas\backend\services\altimeter_service.py`

Add this method to the AltimeterService class:

```python
def get_context_for_email(self, sender: str, subject: str) -> Dict[str, Any]:
    """
    Get project and contact context for an email.
    Used by DraftAgent for "The Lens" context injection.
    """
    context = {
        "project": None,
        "company_role": "Unknown",
        "file_context": ""
    }

    # 1. Parse subject for project IDs
    parsed = self.parse_email_for_project(subject)

    if parsed["project_ids"]:
        project_id = parsed["project_ids"][0]
        project = self.get_project_details(project_id)
        if project:
            context["project"] = {
                "number": project.get("project_number"),
                "name": project.get("project_name"),
                "status": project.get("status"),
                "customer": project.get("customer_name")
            }

    # 2. Try to identify sender role from Altimeter contacts
    try:
        # Extract email from "Name <email>" format if needed
        email_addr = sender
        if '<' in sender:
            email_addr = sender.split('<')[1].rstrip('>')

        # Query Altimeter for contact info
        res = requests.get(f"{self.api_base_url}/api/contacts/", params={"email": email_addr})
        if res.status_code == 200:
            contacts = res.json()
            if contacts:
                contact = contacts[0]
                context["company_role"] = f"{contact.get('role', 'Contact')} at {contact.get('company', 'Unknown')}"
    except Exception as e:
        print(f"[AltimeterService] Contact lookup failed: {e}")

    # 3. Get file context if project found
    if context["project"]:
        try:
            project_id = context["project"]["number"]
            # Fetch recent project activity from Altimeter
            res = requests.get(f"{self.api_base_url}/api/projects/{project_id}/activity")
            if res.status_code == 200:
                activity = res.json()
                context["file_context"] = self._format_activity_context(activity)
        except:
            pass

    return context

def _format_activity_context(self, activity: dict) -> str:
    """Format project activity into context string for AI."""
    lines = []

    if activity.get("recent_logs"):
        lines.append("Recent Daily Logs:")
        for log in activity["recent_logs"][:3]:
            lines.append(f"  - {log.get('date')}: {log.get('summary')}")

    if activity.get("open_rfis"):
        lines.append(f"Open RFIs: {len(activity['open_rfis'])}")

    if activity.get("pending_submittals"):
        lines.append(f"Pending Submittals: {len(activity['pending_submittals'])}")

    if activity.get("customer_contact"):
        c = activity["customer_contact"]
        lines.append(f"Customer Contact: {c.get('name')} ({c.get('email')})")

    return "\n".join(lines) if lines else "No recent activity found."
```

**Validation**: After adding this method, test with:
```bash
curl -X POST http://localhost:4201/api/v1/agents/draft \
  -H "Content-Type: application/json" \
  -d '{"subject": "Project 25-0308 Update", "sender": "test@example.com", "body": "Status update needed.", "instructions": "Reply professionally"}'
```

Expected: Should return `200 OK` with generated draft text.

---

#### Task 1.2: Fix Test Suite
**File**: `C:\Users\mhkem\.atlas\backend\tests\conftest.py`

Update conftest.py to properly configure Python path:

```python
import sys
import os
import pytest

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_path)

# Also add project root
root_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root_path)

@pytest.fixture
def test_db():
    """Provide test database session"""
    from database.database import SessionLocal, engine, Base
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def api_client():
    """Provide FastAPI test client"""
    from fastapi.testclient import TestClient
    from core.app import app
    return TestClient(app)
```

**File**: `C:\Users\mhkem\.atlas\backend\tests\test_atlas_flow.py`

Rewrite test file to use current API:

```python
import pytest
from fastapi.testclient import TestClient

def test_email_list(api_client):
    """Test email list endpoint returns emails"""
    response = api_client.get("/api/v1/email/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_email_sync(api_client):
    """Test email sync endpoint"""
    response = api_client.post("/api/v1/email/sync")
    assert response.status_code == 200
    data = response.json()
    assert "synced" in data or "timestamp" in data

def test_system_health(api_client):
    """Test system health endpoint"""
    response = api_client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("atlas") == "healthy"

def test_draft_agent(api_client):
    """Test draft generation endpoint"""
    response = api_client.post("/api/v1/agents/draft", json={
        "subject": "Test Subject",
        "sender": "test@example.com",
        "body": "Test body content",
        "instructions": "Reply briefly"
    })
    assert response.status_code == 200
    data = response.json()
    assert "draft_text" in data
    assert data.get("status") == "generated"

def test_knowledge_docs(api_client):
    """Test knowledge base document listing"""
    response = api_client.get("/api/v1/knowledge/docs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Validation**: Run tests with:
```bash
cd C:\Users\mhkem\.atlas
python -m pytest backend/tests/ -v
```

---

### PHASE 2: Implement Task Agent

#### Task 2.1: Implement AI Task Extraction
**File**: `C:\Users\mhkem\.atlas\backend\agents\task_agent.py`

Replace current placeholder with full implementation:

```python
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from agents.base import BaseAgent
from services.ai_service import ai_service
from services.altimeter_service import altimeter_service

class TaskAgent(BaseAgent):
    """
    AI Agent for extracting and managing tasks from emails.
    """

    def __init__(self):
        super().__init__(agent_name="TaskAgent")
        self.model_name = "gemini-2.0-flash"

    async def extract_tasks_from_email(self, email: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract action items from an email using AI.
        """
        subject = email.get('subject', '')
        body = email.get('body_text', '') or email.get('body', '')
        sender = email.get('from_address', '')

        # Get project context if available
        parsed = altimeter_service.parse_email_for_project(f"{subject} {body}")
        project_context = ""
        project_id = None

        if parsed["project_ids"]:
            project_id = parsed["project_ids"][0]
            project = altimeter_service.get_project_details(project_id)
            if project:
                project_context = f"Project: {project.get('project_name')} ({project_id})"

        prompt = f"""
        Analyze this email and extract any action items or tasks.

        Email:
        From: {sender}
        Subject: {subject}
        Body:
        {body[:2000]}  # Limit body length for API

        {project_context}

        Extract tasks in the following JSON format:
        {{
            "tasks": [
                {{
                    "title": "Brief task title (max 50 chars)",
                    "description": "Detailed description of what needs to be done",
                    "priority": "high|medium|low",
                    "due_date": "YYYY-MM-DD or null if not mentioned",
                    "estimated_hours": 1.0,
                    "category": "rfi|submittal|coordination|budget|general"
                }}
            ]
        }}

        Rules:
        - Extract explicit action items (requests, deadlines, questions needing response)
        - Set priority based on urgency keywords or deadlines
        - For RFIs/Submittals, set category appropriately
        - If no clear tasks, return empty array
        - Only return valid JSON
        """

        try:
            response = await ai_service.generate_content(prompt)

            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())
            tasks = data.get("tasks", [])

            # Enrich tasks with email metadata
            for task in tasks:
                task["email_id"] = email.get("email_id")
                task["project_id"] = project_id
                task["created_from"] = "email"
                task["source_email_subject"] = subject

            return tasks

        except json.JSONDecodeError as e:
            print(f"[TaskAgent] Failed to parse AI response: {e}")
            return []
        except Exception as e:
            print(f"[TaskAgent] Task extraction failed: {e}")
            return []

    async def prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Reorder and enhance tasks with AI-powered prioritization.
        """
        if not tasks:
            return []

        priority_map = {"high": 3, "medium": 2, "low": 1}

        # Sort by priority and due date
        def sort_key(task):
            priority_score = priority_map.get(task.get("priority", "medium"), 2)
            due_date = task.get("due_date")
            if due_date:
                try:
                    days_until = (datetime.strptime(due_date, "%Y-%m-%d") - datetime.now()).days
                    # Boost priority for items due soon
                    if days_until <= 1:
                        priority_score += 2
                    elif days_until <= 3:
                        priority_score += 1
                except:
                    pass
            return -priority_score  # Negative for descending

        return sorted(tasks, key=sort_key)

    async def estimate_effort(self, task: Dict) -> float:
        """
        AI-powered effort estimation for a task.
        """
        title = task.get("title", "")
        description = task.get("description", "")
        category = task.get("category", "general")

        prompt = f"""
        Estimate the effort in hours for this construction electrical contracting task:

        Title: {title}
        Description: {description}
        Category: {category}

        Consider:
        - RFIs typically take 1-4 hours depending on complexity
        - Submittals take 2-8 hours for review and compilation
        - Coordination meetings are typically 1-2 hours
        - Budget items vary widely (1-8+ hours)

        Return ONLY a number representing estimated hours (e.g., "2.5")
        """

        try:
            response = await ai_service.generate_content(prompt)
            hours = float(response.strip())
            return min(max(hours, 0.5), 40)  # Clamp between 0.5 and 40 hours
        except:
            # Default estimates by category
            defaults = {
                "rfi": 2.0,
                "submittal": 4.0,
                "coordination": 1.5,
                "budget": 3.0,
                "general": 1.0
            }
            return defaults.get(category, 1.0)

# Singleton
task_agent = TaskAgent()
```

---

#### Task 2.2: Create Task Routes
**File**: `C:\Users\mhkem\.atlas\backend\api\task_routes.py` (NEW FILE)

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database.database import get_db
from database.models import Task, Email
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[str] = None
    project_id: Optional[str] = None
    email_id: Optional[int] = None
    estimated_hours: Optional[float] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    actual_hours: Optional[float] = None

@router.get("/list")
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get tasks with filtering"""
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)

    # Order by priority then due date
    query = query.order_by(Task.due_date.asc().nullslast())

    return query.offset(offset).limit(limit).all()

@router.get("/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get single task"""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/create")
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status="todo",
        priority=task_data.priority,
        project_id=task_data.project_id,
        email_id=task_data.email_id,
        estimated_hours=task_data.estimated_hours,
        created_from="manual"
    )

    if task_data.due_date:
        try:
            task.due_date = datetime.strptime(task_data.due_date, "%Y-%m-%d")
        except:
            pass

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/{task_id}")
async def update_task(task_id: int, updates: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if updates.title:
        task.title = updates.title
    if updates.description:
        task.description = updates.description
    if updates.status:
        task.status = updates.status
        if updates.status == "done":
            task.completed_at = datetime.now()
    if updates.priority:
        task.priority = updates.priority
    if updates.due_date:
        try:
            task.due_date = datetime.strptime(updates.due_date, "%Y-%m-%d")
        except:
            pass
    if updates.actual_hours:
        task.actual_hours = updates.actual_hours

    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"deleted": True}

@router.post("/extract/{email_id}")
async def extract_tasks_from_email(email_id: int, db: Session = Depends(get_db)):
    """Extract tasks from an email using AI"""
    from agents.task_agent import task_agent

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Convert to dict for agent
    email_dict = {
        "email_id": email.email_id,
        "subject": email.subject,
        "body_text": email.body_text,
        "from_address": email.from_address
    }

    tasks = await task_agent.extract_tasks_from_email(email_dict)

    # Save extracted tasks to database
    created_tasks = []
    for task_data in tasks:
        task = Task(
            title=task_data.get("title", "Untitled Task"),
            description=task_data.get("description"),
            status="todo",
            priority=task_data.get("priority", "medium"),
            category=task_data.get("category"),
            project_id=task_data.get("project_id"),
            email_id=email_id,
            estimated_hours=task_data.get("estimated_hours"),
            created_from="email"
        )

        if task_data.get("due_date"):
            try:
                task.due_date = datetime.strptime(task_data["due_date"], "%Y-%m-%d")
            except:
                pass

        db.add(task)
        created_tasks.append(task)

    db.commit()

    return {
        "extracted": len(created_tasks),
        "tasks": [{"task_id": t.task_id, "title": t.title, "priority": t.priority} for t in created_tasks]
    }
```

---

#### Task 2.3: Register Task Routes
**File**: `C:\Users\mhkem\.atlas\backend\api\routes.py`

Add after line 73 (after email_router include):

```python
from api.task_routes import router as task_router
router.include_router(task_router, prefix="/tasks", tags=["Tasks"])
```

**Validation**:
```bash
# List tasks
curl http://localhost:4201/api/v1/tasks/list

# Create task
curl -X POST http://localhost:4201/api/v1/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"title": "Review RFI-001", "priority": "high", "project_id": "25-0308"}'

# Extract tasks from email
curl -X POST http://localhost:4201/api/v1/tasks/extract/116
```

---

### PHASE 3: Implement Calendar Agent

#### Task 3.1: Create Calendar Agent
**File**: `C:\Users\mhkem\.atlas\backend\agents\calendar_agent.py` (NEW FILE)

```python
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from agents.base import BaseAgent
from services.ai_service import ai_service
from services.google_service import google_service
from database.database import get_db
from database.models import CalendarEvent
import json

class CalendarAgent(BaseAgent):
    """
    AI Agent for calendar management and meeting scheduling.
    """

    def __init__(self):
        super().__init__(agent_name="CalendarAgent")

    async def sync_google_calendar(self) -> Dict[str, Any]:
        """
        Sync events from Google Calendar.
        """
        try:
            result = google_service.sync_calendar()
            return result
        except Exception as e:
            return {"error": str(e), "synced": 0}

    async def detect_conflicts(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Check for overlapping events in the given time range.
        """
        db = next(get_db())

        conflicts = db.query(CalendarEvent).filter(
            CalendarEvent.start_time < end_time,
            CalendarEvent.end_time > start_time
        ).all()

        return [
            {
                "event_id": e.event_id,
                "title": e.title,
                "start": e.start_time.isoformat() if e.start_time else None,
                "end": e.end_time.isoformat() if e.end_time else None
            }
            for e in conflicts
        ]

    async def suggest_meeting_times(
        self,
        duration_minutes: int,
        date_range_start: datetime,
        date_range_end: datetime,
        prefer_morning: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Suggest available time slots for a meeting.
        """
        db = next(get_db())

        # Get existing events in range
        existing = db.query(CalendarEvent).filter(
            CalendarEvent.start_time >= date_range_start,
            CalendarEvent.end_time <= date_range_end
        ).order_by(CalendarEvent.start_time).all()

        # Build list of busy times
        busy_times = [(e.start_time, e.end_time) for e in existing if e.start_time and e.end_time]

        # Find free slots
        suggestions = []
        current_date = date_range_start.date()
        end_date = date_range_end.date()

        while current_date <= end_date and len(suggestions) < 5:
            # Define working hours (7 AM - 6 PM)
            day_start = datetime.combine(current_date, datetime.min.time().replace(hour=7))
            day_end = datetime.combine(current_date, datetime.min.time().replace(hour=18))

            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # Find gaps in schedule
            check_time = day_start
            while check_time + timedelta(minutes=duration_minutes) <= day_end:
                slot_end = check_time + timedelta(minutes=duration_minutes)

                # Check if slot conflicts with any existing event
                is_free = True
                for busy_start, busy_end in busy_times:
                    if check_time < busy_end and slot_end > busy_start:
                        is_free = False
                        # Jump past this busy period
                        check_time = busy_end
                        break

                if is_free:
                    # Prefer morning slots
                    score = 1.0
                    if prefer_morning and check_time.hour < 12:
                        score = 1.5

                    suggestions.append({
                        "start": check_time.isoformat(),
                        "end": slot_end.isoformat(),
                        "score": score,
                        "label": f"{check_time.strftime('%a %b %d, %I:%M %p')} - {slot_end.strftime('%I:%M %p')}"
                    })

                    if len(suggestions) >= 5:
                        break

                    # Skip ahead to find next slot
                    check_time = slot_end + timedelta(minutes=30)
                else:
                    check_time += timedelta(minutes=15)

            current_date += timedelta(days=1)

        # Sort by score
        suggestions.sort(key=lambda x: -x["score"])
        return suggestions[:5]

    async def extract_meeting_from_email(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect meeting requests in email and extract event details.
        """
        subject = email.get("subject", "")
        body = email.get("body_text", "")
        sender = email.get("from_address", "")

        prompt = f"""
        Analyze this email to detect if it's requesting or scheduling a meeting.

        Email:
        From: {sender}
        Subject: {subject}
        Body:
        {body[:1500]}

        If a meeting is mentioned, extract details in this JSON format:
        {{
            "is_meeting_request": true,
            "title": "Meeting title",
            "suggested_date": "YYYY-MM-DD or null",
            "suggested_time": "HH:MM (24h) or null",
            "duration_minutes": 60,
            "location": "Location or null",
            "attendees": ["email1@example.com"],
            "description": "Meeting purpose"
        }}

        If no meeting is mentioned, return:
        {{
            "is_meeting_request": false
        }}

        Only return valid JSON.
        """

        try:
            response = await ai_service.generate_content(prompt)

            # Clean response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            if data.get("is_meeting_request"):
                data["source_email_id"] = email.get("email_id")
                return data
            return None

        except Exception as e:
            print(f"[CalendarAgent] Meeting extraction failed: {e}")
            return None

# Singleton
calendar_agent = CalendarAgent()
```

---

#### Task 3.2: Create Calendar Routes
**File**: `C:\Users\mhkem\.atlas\backend\api\calendar_routes.py` (NEW FILE)

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from database.database import get_db
from database.models import CalendarEvent
from sqlalchemy.orm import Session

router = APIRouter()

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str  # ISO format
    end_time: str
    project_id: Optional[str] = None
    attendees: Optional[List[str]] = None

class SuggestTimesRequest(BaseModel):
    duration_minutes: int = 60
    date_range_days: int = 7
    prefer_morning: bool = True

@router.get("/events")
async def get_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get calendar events with filtering"""
    query = db.query(CalendarEvent)

    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(CalendarEvent.start_time >= start)
        except:
            pass

    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(CalendarEvent.end_time <= end)
        except:
            pass

    if project_id:
        query = query.filter(CalendarEvent.project_id == project_id)

    query = query.order_by(CalendarEvent.start_time)
    return query.limit(limit).all()

@router.get("/{event_id}")
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get single event"""
    event = db.query(CalendarEvent).filter(CalendarEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/sync")
async def sync_calendar():
    """Trigger Google Calendar sync"""
    from agents.calendar_agent import calendar_agent
    result = await calendar_agent.sync_google_calendar()
    return result

@router.post("/create")
async def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """Create a new calendar event"""
    try:
        start = datetime.fromisoformat(event_data.start_time)
        end = datetime.fromisoformat(event_data.end_time)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

    event = CalendarEvent(
        title=event_data.title,
        description=event_data.description,
        location=event_data.location,
        start_time=start,
        end_time=end,
        project_id=event_data.project_id,
        attendees=event_data.attendees,
        status="confirmed"
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.post("/suggest-times")
async def suggest_meeting_times(request: SuggestTimesRequest):
    """AI-powered meeting time suggestions"""
    from agents.calendar_agent import calendar_agent

    now = datetime.now()
    end = now + timedelta(days=request.date_range_days)

    suggestions = await calendar_agent.suggest_meeting_times(
        duration_minutes=request.duration_minutes,
        date_range_start=now,
        date_range_end=end,
        prefer_morning=request.prefer_morning
    )

    return {"suggestions": suggestions}

@router.post("/check-conflicts")
async def check_conflicts(start_time: str, end_time: str):
    """Check for scheduling conflicts"""
    from agents.calendar_agent import calendar_agent

    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")

    conflicts = await calendar_agent.detect_conflicts(start, end)
    return {"conflicts": conflicts, "has_conflicts": len(conflicts) > 0}

@router.post("/extract-from-email/{email_id}")
async def extract_meeting_from_email(email_id: int, db: Session = Depends(get_db)):
    """Extract meeting details from an email"""
    from agents.calendar_agent import calendar_agent
    from database.models import Email

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email_dict = {
        "email_id": email.email_id,
        "subject": email.subject,
        "body_text": email.body_text,
        "from_address": email.from_address
    }

    meeting = await calendar_agent.extract_meeting_from_email(email_dict)

    if meeting:
        return {"found": True, "meeting": meeting}
    return {"found": False, "message": "No meeting detected in email"}
```

---

#### Task 3.3: Register Calendar Routes
**File**: `C:\Users\mhkem\.atlas\backend\api\routes.py`

Add after task_router include:

```python
from api.calendar_routes import router as calendar_router
router.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])
```

---

### PHASE 4: Implement Vector Search (ChromaDB)

#### Task 4.1: Create Search Service
**File**: `C:\Users\mhkem\.atlas\backend\services\search_service.py` (NEW FILE)

```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os

class SearchService:
    """
    Vector search service using ChromaDB for semantic email and file search.
    """

    def __init__(self):
        # Initialize ChromaDB with persistent storage
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "databases", "vectors")
        os.makedirs(db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=db_path)

        # Create collections
        self.email_collection = self.client.get_or_create_collection(
            name="emails",
            metadata={"description": "Email content embeddings"}
        )

        self.file_collection = self.client.get_or_create_collection(
            name="files",
            metadata={"description": "Document and file embeddings"}
        )

    def index_email(self, email: Dict[str, Any]) -> bool:
        """
        Index an email in the vector store.
        """
        try:
            email_id = str(email.get("email_id"))

            # Combine subject and body for embedding
            content = f"{email.get('subject', '')} {email.get('body_text', '')}"

            # Metadata for filtering
            metadata = {
                "email_id": email_id,
                "from_address": email.get("from_address", ""),
                "date_received": email.get("date_received", ""),
                "project_id": email.get("project_id") or "",
                "category": email.get("category") or ""
            }

            self.email_collection.upsert(
                ids=[email_id],
                documents=[content],
                metadatas=[metadata]
            )

            return True
        except Exception as e:
            print(f"[SearchService] Email indexing failed: {e}")
            return False

    def index_file(self, file: Dict[str, Any], content: str) -> bool:
        """
        Index a file/document in the vector store.
        """
        try:
            file_id = str(file.get("file_id") or file.get("filename"))

            metadata = {
                "file_id": file_id,
                "filename": file.get("filename", ""),
                "file_path": file.get("file_path", ""),
                "project_id": file.get("project_id") or "",
                "mime_type": file.get("mime_type") or ""
            }

            # Chunk large documents
            chunks = self._chunk_text(content, chunk_size=500)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_id}_chunk_{i}"
                self.file_collection.upsert(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[{**metadata, "chunk_index": i}]
                )

            return True
        except Exception as e:
            print(f"[SearchService] File indexing failed: {e}")
            return False

    def search_emails(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across emails.
        """
        try:
            where_filter = None
            if project_id:
                where_filter = {"project_id": project_id}

            results = self.email_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )

            # Format results
            formatted = []
            if results and results.get("ids"):
                for i, email_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "email_id": email_id,
                        "score": results["distances"][0][i] if results.get("distances") else None,
                        "snippet": results["documents"][0][i][:200] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {}
                    })

            return formatted
        except Exception as e:
            print(f"[SearchService] Email search failed: {e}")
            return []

    def search_files(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across files/documents.
        """
        try:
            where_filter = None
            if project_id:
                where_filter = {"project_id": project_id}

            results = self.file_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )

            # Format and dedupe by file
            formatted = []
            seen_files = set()

            if results and results.get("ids"):
                for i, chunk_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    file_id = metadata.get("file_id")

                    if file_id not in seen_files:
                        seen_files.add(file_id)
                        formatted.append({
                            "file_id": file_id,
                            "filename": metadata.get("filename"),
                            "file_path": metadata.get("file_path"),
                            "score": results["distances"][0][i] if results.get("distances") else None,
                            "snippet": results["documents"][0][i][:200] if results.get("documents") else ""
                        })

            return formatted
        except Exception as e:
            print(f"[SearchService] File search failed: {e}")
            return []

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks for embedding.
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1

            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [text]

    def get_stats(self) -> Dict[str, int]:
        """
        Get index statistics.
        """
        return {
            "emails_indexed": self.email_collection.count(),
            "files_indexed": self.file_collection.count()
        }

# Singleton
search_service = SearchService()
```

---

#### Task 4.2: Create AI/Search Routes
**File**: `C:\Users\mhkem\.atlas\backend\api\ai_routes.py` (NEW FILE)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.search_service import search_service
from services.ai_service import ai_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    limit: int = 10

class ChatRequest(BaseModel):
    message: str
    project_id: Optional[str] = None

@router.post("/search/emails")
async def search_emails(request: SearchRequest):
    """Semantic search across emails"""
    results = search_service.search_emails(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit
    )
    return {"results": results, "count": len(results)}

@router.post("/search/files")
async def search_files(request: SearchRequest):
    """Semantic search across files"""
    results = search_service.search_files(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit
    )
    return {"results": results, "count": len(results)}

@router.get("/search/stats")
async def get_search_stats():
    """Get vector index statistics"""
    return search_service.get_stats()

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """Chat with AI assistant using RAG"""
    # 1. Search for relevant context
    email_results = search_service.search_emails(request.message, request.project_id, limit=5)
    file_results = search_service.search_files(request.message, request.project_id, limit=3)

    # 2. Build context
    context_parts = []

    if email_results:
        context_parts.append("Relevant Emails:")
        for r in email_results[:3]:
            context_parts.append(f"- {r.get('snippet', '')}")

    if file_results:
        context_parts.append("\nRelevant Documents:")
        for r in file_results[:2]:
            context_parts.append(f"- {r.get('filename', '')}: {r.get('snippet', '')}")

    context = "\n".join(context_parts) if context_parts else "No relevant context found."

    # 3. Generate response
    prompt = f"""
    You are Atlas, a personal AI assistant for Davis Electric (construction electrical contractor).

    User Question: {request.message}

    {"Project Context: " + request.project_id if request.project_id else ""}

    Relevant Information from Knowledge Base:
    {context}

    Provide a helpful, accurate response. If the context doesn't contain enough information to answer fully, say so.
    """

    response = await ai_service.generate_content(prompt)

    return {
        "response": response,
        "sources": {
            "emails": len(email_results),
            "files": len(file_results)
        }
    }

@router.post("/summarize/email/{email_id}")
async def summarize_email(email_id: int):
    """AI-powered email summarization"""
    from database.database import get_db
    from database.models import Email

    db = next(get_db())
    email = db.query(Email).filter(Email.email_id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    prompt = f"""
    Summarize this email in 2-3 sentences:

    From: {email.from_address}
    Subject: {email.subject}
    Body: {email.body_text[:2000] if email.body_text else 'No content'}

    Key points:
    1. Main topic/request
    2. Any action items or deadlines
    3. Urgency level (if applicable)
    """

    summary = await ai_service.generate_content(prompt)

    return {
        "email_id": email_id,
        "summary": summary
    }
```

---

#### Task 4.3: Register AI Routes
**File**: `C:\Users\mhkem\.atlas\backend\api\routes.py`

Add after calendar_router include:

```python
from api.ai_routes import router as ai_router
router.include_router(ai_router, prefix="/ai", tags=["AI Assistant"])
```

---

### FINAL CHECKLIST

After completing all phases, verify:

- [ ] `GET /api/v1/system/health` returns healthy
- [ ] `POST /api/v1/agents/draft` generates drafts with project context
- [ ] `GET /api/v1/tasks/list` returns tasks
- [ ] `POST /api/v1/tasks/extract/{email_id}` extracts tasks from email
- [ ] `GET /api/v1/calendar/events` returns calendar events
- [ ] `POST /api/v1/calendar/suggest-times` returns meeting suggestions
- [ ] `POST /api/v1/ai/search/emails` performs semantic search
- [ ] `POST /api/v1/ai/chat` responds with context
- [ ] `python -m pytest backend/tests/ -v` passes all tests

---

## DEPENDENCIES TO ADD

**File**: `C:\Users\mhkem\.atlas\requirements.txt`

Ensure these are present:
```
chromadb>=0.4.0
```

Install with:
```bash
pip install chromadb
```

---

## IMPLEMENTATION ORDER

1. **Task 1.1** - Fix `get_context_for_email()` (unblocks draft agent)
2. **Task 1.2** - Fix test suite (enables validation)
3. **Task 2.1-2.3** - Implement task agent and routes
4. **Task 3.1-3.3** - Implement calendar agent and routes
5. **Task 4.1-4.3** - Implement vector search and AI routes

Each phase should be validated before moving to the next.

---

**Generated by Claude Opus 4.5 - 2026-01-26**
