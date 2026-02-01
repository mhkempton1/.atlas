# Atlas: Personal AI Assistant Platform

## System Architecture Specification v2.0

---

## EXECUTIVE SUMMARY

**Atlas** is an intelligent personal AI assistant system designed to manage work and personal life through unified email intelligence, calendar management, task coordination, and context-aware project assistance. Built on a modern FastAPI + React stack with Gemini AI integration.

**Purpose**: Personal productivity multiplication through AI assistance  
**Scope**: Email, calendar, tasks, project context, file management  
**Integration**: Gmail, Google Calendar, Altimeter (work context), file systems

---

## SYSTEM ARCHITECTURE

```text
c:\Users\mhkem\.atlas/
├── backend/                # FastAPI Python backend
│   ├── agents/            # AI agents
│   ├── api/               # REST endpoints
│   ├── core/              # App core
│   ├── database/          # Data models
│   ├── security/          # Auth
│   ├── services/          # Business logic
│   └── tools/             # Tool integrations
├── frontend/              # React/Vite UI
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── store/
│   └── public/
├── data/                  # Data storage
│   ├── databases/         # SQLite databases
│   │   └── vectors/       # ChromaDB vector store
│   ├── files/             # File storage
│   └── logs/              # System logs
├── config/                # Configuration
│   ├── secrets.json       # Credentials (encrypted)
│   └── app_config.json
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

---

## 1. BACKEND ARCHITECTURE

### Core Components

**FastAPI Application** (Port 4201)

- RESTful API design
- Automatic OpenAPI docs
- WebSocket support (real-time updates)
- Background task processing
- Rate limiting & caching

### AI Agents (`agents/`)

```python
agents/
├── draft_agent.py         # Email draft generation
├── calendar_agent.py      # Calendar management
├── task_agent.py          # Task prioritization
├── project_agent.py       # Project assistance
├── research_agent.py      # Information gathering
└── file_agent.py          # File organization
```

#### Draft Agent

- Reads incoming email context
- Analyzes sender/subject/body
- Generates contextually appropriate draft
- Uses Gemini 2.0 Flash for intelligence
- Falls back to Ollama local model if API unavailable
- Supports multiple draft variations
- Review workflow before sending

#### Project Agent

- Integrates with Altimeter for work context
- Provides project-specific assistance
- Accesses project files and data
- Suggests next actions based on project state
- Alerts for deadlines and blockers

#### Calendar Agent

- Analyzes calendar for conflicts
- Suggests optimal meeting times
- Tracks time commitments
- Integrates with email for meeting detection
- Separates work vs personal

#### Task Agent

- Prioritizes tasks using AI
- Suggests task breakdown for complex items
- Tracks dependencies
- Estimates effort/time
- Integrates with email (tasks from emails)

### Services Layer (`services/`)

```python
services/
├── email_service.py       # Email CRUD operations
├── calendar_service.py    # Calendar sync & management
├── task_service.py        # Task management
├── file_service.py        # File operations
├── search_service.py      # Vector search (RAG)
└── sync_service.py        # Email/calendar sync
```

### Database Schema

```sql
-- Enhanced email database (never truncate)
CREATE TABLE emails (
    email_id INTEGER PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    thread_id TEXT,
    gmail_id TEXT UNIQUE,          -- Gmail message ID
    from_address TEXT,
    from_name TEXT,
    to_addresses JSON,             -- Array of recipients
    cc_addresses JSON,
    bcc_addresses JSON,
    subject TEXT,
    body_text TEXT,                -- NEVER TRUNCATE
    body_html TEXT,                -- NEVER TRUNCATE
    snippet TEXT,                  -- 200 char preview
    date_received DATETIME,
    date_sent DATETIME,
    labels JSON,                   -- Gmail labels
    category TEXT,                 -- Auto-categorized
    importance TEXT,               -- High/Medium/Low
    has_attachments BOOLEAN,
    attachment_count INTEGER,
    is_read BOOLEAN,
    is_starred BOOLEAN,
    is_draft BOOLEAN,
    project_id TEXT,               -- Link to Altimeter project
    contact_id INTEGER,            -- Link to contacts
    raw_eml BLOB,                  -- Full EML for preservation
    vector_embedding BLOB,         -- For semantic search
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    synced_at DATETIME
);

CREATE TABLE email_attachments (
    attachment_id INTEGER PRIMARY KEY,
    email_id INTEGER,
    filename TEXT,
    file_size INTEGER,
    mime_type TEXT,
    file_path TEXT,               -- Stored location
    file_hash TEXT,                -- SHA256 for dedup
    gmail_attachment_id TEXT,      -- Gmail reference
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

CREATE TABLE email_threads (
    thread_id TEXT PRIMARY KEY,
    subject TEXT,
    participants JSON,             -- All email addresses involved
    first_email_date DATETIME,
    last_email_date DATETIME,
    email_count INTEGER,
    is_archived BOOLEAN,
    project_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE drafts (
    draft_id INTEGER PRIMARY KEY,
    email_id INTEGER,             -- Original email if reply
    recipient TEXT,
    cc TEXT,
    bcc TEXT,
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    generated_by TEXT,            -- 'ai' or 'user'
    ai_model TEXT,                 -- 'gemini-2.0-flash'
    generation_prompt TEXT,        -- Prompt used
    status TEXT,                   -- draft/scheduled/sent
    scheduled_time DATETIME,
    sent_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE contacts (
    contact_id INTEGER PRIMARY KEY,
    name TEXT,
    email_address TEXT UNIQUE,
    phone TEXT,
    company TEXT,
    role TEXT,
    category TEXT,                 -- work/personal/vendor/customer
    altimeter_customer_id INTEGER, -- Link to Altimeter
    altimeter_vendor_id INTEGER,
    last_contact_date DATETIME,
    email_count INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    status TEXT,                   -- todo/in_progress/done/blocked
    priority TEXT,                 -- high/medium/low
    category TEXT,                 -- work/personal/home
    project_id TEXT,               -- Link to Altimeter if work
    due_date DATE,
    estimated_hours REAL,
    actual_hours REAL,
    parent_task_id INTEGER,        -- For subtasks
    email_id INTEGER,              -- Source email if applicable
    created_from TEXT,             -- 'manual', 'email', 'ai_suggested'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id)
);

CREATE TABLE calendar_events (
    event_id INTEGER PRIMARY KEY,
    google_event_id TEXT UNIQUE,
    calendar_id TEXT,              -- Which calendar (work/personal)
    title TEXT,
    description TEXT,
    location TEXT,
    start_time DATETIME,
    end_time DATETIME,
    all_day BOOLEAN,
    attendees JSON,                -- Array of email addresses
    organizer TEXT,
    status TEXT,                   -- confirmed/tentat ive/cancelled
    project_id TEXT,               -- Link to Altimeter
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    synced_at DATETIME
);

CREATE TABLE files (
    file_id INTEGER PRIMARY KEY,
    filename TEXT,
    file_path TEXT,
    file_size INTEGER,
    mime_type TEXT,
    file_hash TEXT,
    category TEXT,                 -- document/image/pdf/etc
    project_id TEXT,
    email_id INTEGER,
    tags JSON,
    vector_embedding BLOB,         -- For semantic search
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
```

### Email Truncation Rules

**NEVER TRUNCATE:**

- Email body (body_text, body_html)
- Email headers
- Attachment filenames
- Thread information

**CONDITIONAL ARCHIVING:**

- Emails older than 2 years: Move to compressed archive files (.zip)
- Keep database record with reference to archive file
- On-demand retrieval from archive

**Storage Strategy:**

```python
def should_archive_email(email_date):
    """Archive emails older than 2 years"""
    return (datetime.now() - email_date).days > 730

def archive_old_emails():
    """Monthly job to compress old emails"""
    old_emails = get_emails_older_than(730)
for email in old_emails:
        # Save full EML to archive
        archive_path = f"archives/{email.year}/{email.month}.zip"
        add_to_archive(archive_path, email.raw_eml)
        
        # Update database record
        email.archived = True
        email.archive_path = archive_path
        email.raw_eml = None  # Clear from active DB
```

---

## 2. FRONTEND ARCHITECTURE

### React Application (Port 4202)

```text
frontend/src/
├── components/
│   ├── email/
│   │   ├── EmailList.jsx
│   │   ├── EmailView.jsx
│   │   ├── ComposeDraft.jsx
│   │   └── ThreadView.jsx
│   ├── calendar/
│   │   ├── CalendarView.jsx
│   │   ├── EventDetail.jsx
│   │   └── MeetingScheduler.jsx
│   ├── tasks/
│   │   ├── TaskList.jsx
│   │   ├── TaskBoard.jsx      # Kanban view
│   │   └── TaskDetail.jsx
│   ├── dashboard/
│   │   ├── Overview.jsx
│   │   ├── AIAssistant.jsx
│   │   └── QuickActions.jsx
│   └── shared/
│       ├── SearchBar.jsx
│       └── Notifications.jsx
├── pages/
│   ├── Dashboard.jsx
│   ├── Inbox.jsx
│   ├── Calendar.jsx
│   ├── Tasks.jsx
│   └── Files.jsx
├── services/
│   ├── api.js              # API client
│   ├── websocket.js        # Real-time updates
│   └── auth.js             # Authentication
└── store/                  # State management
    ├── emailStore.js
    ├── taskStore.js
    └── userStore.js
```

### Key Features

#### Email Intelligence

- Smart categorization (work/personal/urgent/spam)
- Thread grouping
- AI-powered search
- Quick replies with AI suggestions
- Draft generation with review

#### Calendar Management

- Unified view (work + personal)
- Conflict detection
- Smart scheduling suggestions
- Meeting preparation (pull related emails/files)

#### Task Management

- Auto-extract tasks from emails
- Priority recommendations
- Time blocking suggestions
- Integration with calendar

#### AI Assistant Chat

- Conversational interface
- "Find all emails about project X"
- "Schedule meeting with Y for next week"
- "Summarize this email thread"
- "Draft response to this email"

---

## 3. INTEGRATION WITH ALTIMETER

### Work Context Integration

```python
# backend/integrations/altimeter.py

class AltimeterIntegration:
    """Connect Atlas to Altimeter for work context"""
    
    def __init__(self):
        self.altimeter_db = "c:/Users/mhkem/.altimeter/database/altimeter.db"
        self.project_cache = {}
    
    def link_email_to_project(self, email):
        """Auto-link email to Altimeter project"""
        # Check for project number in subject/body
        project_numbers = extract_project_numbers(email.subject + email.body)
        
        for proj_num in project_numbers:
            project = self.get_project(proj_num)
            if project:
                email.project_id = proj_num
                email.category = 'work'
                return proj_num
        
        # Check sender against Altimeter customers/vendors
        contact = self.find_contact(email.from_address)
        if contact:
            # Find active projects with this contact
            projects = self.get_projects_by_contact(contact.id)
            if projects:
                email.project_id = projects[0].project_id
                return projects[0].project_id
        
        return None
    
    def get_project_context(self, project_id):
        """Get project details for AI assistant"""
        # Query Altimeter database
        project = query_altimeter_db(f"""
            SELECT * FROM Projects WHERE ProjectID = '{project_id}'
        """)
        
        # Get recent activity
        recent_logs = query_altimeter_db(f"""
            SELECT * FROM DailyLogs 
            WHERE ProjectID = '{project_id}'
            ORDER BY LogDate DESC LIMIT 5
        """)
        
        return {
            'project': project,
            'status': project.status,
            'budget': project.budget,
            'schedule': project.schedule,
            'recent_activity': recent_logs
        }
    
    def get_action_items(self, project_id):
        """Get outstanding items for project"""
        return {
            'open_rfis': get_open_rfis(project_id),
            'pending_submittals': get_pending_submittals(project_id),
            'upcoming_deliveries': get_upcoming_deliveries(project_id),
            'overdue_invoices': get_overdue_invoices(project_id)
        }
```

### Bi-Directional Sync

**From Altimeter to Atlas:**

- Project updates trigger email notifications
- New tasks auto-created in Atlas task list
- Calendar events for project milestones

**From Atlas to Altimeter:**

- Email correspondence logged to project
- File attachments linked to project files
- Task completion updates project status

---

## 4. AI CAPABILITIES

### Gemini 2.0 Flash Integration

```python
# backend/ai/gemini_client.py

class GeminiClient:
    """Wrapper for Google Gemini API"""
    
    def generate_draft(self, email_context, instructions):
        """Generate email draft"""
        prompt = f"""
        You are a professional assistant drafting an email response.
        
        Original Email:
        From: {email_context.from_address}
        Subject: {email_context.subject}
        Body: {email_context.body}
        
        Context:
        - This is related to {email_context.project_id or 'personal matter'}
        - Tone should be {instructions.get('tone', 'professional')}
        
        Instructions: {instructions.get('custom', 'Write a thoughtful response')}
        
        Generate a draft email response.
        """
        
        response = self.gemini.generate_content(prompt)
        return response.text
    
    def categorize_email(self, email):
        """AI-powered email categorization"""
        prompt = f"""
        Categorize this email into one of: work, personal, urgent, spam, promotional
        
        From: {email.from_address}
        Subject: {email.subject}
        Body: {email.body[:500]}
        
        Respond with just the category name.
        """
        
        return self.gemini.generate_content(prompt).text.strip().lower()
    
    def extract_tasks(self, email):
        """Extract action items from email"""
        prompt = f"""
        Extract action items or tasks from this email. For each task provide:
        - Task description
        - Priority (high/medium/low)
        - Due date if mentioned
        
        Email:
        Subject: {email.subject}
        Body: {email.body}
        
        Return as JSON array.
        """
        
        return json.loads(self.gemini.generate_content(prompt).text)
```

### Vector Search (RAG)

Using ChromaDB for semantic search across emails, files, and documents:

```python
# backend/services/search_service.py

class SemanticSearch:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.email_collection = self.chroma_client.get_or_create_collection("emails")
        self.file_collection = self.chroma_client.get_or_create_collection("files")
    
    def index_email(self, email):
        """Add email to vector database"""
        text = f"{email.subject} {email.body}"
        self.email_collection.add(
            documents=[text],
            metadatas=[{
                'email_id': email.email_id,
                'from': email.from_address,
                'date': str(email.date_received),
                'project_id': email.project_id
            }],
            ids=[str(email.email_id)]
        )
    
    def search_emails(self, query, filters=None):
        """Semantic search across emails"""
        results = self.email_collection.query(
            query_texts=[query],
            n_results=10,
            where=filters  # e.g., {'project_id': '25-0308'}
        )
        return results
```

---

## 5.DEPLOYMENT

### Local Development

```bash
# Terminal 1 - Atlas Backend
cd c:\Users\mhkem\.atlas\backend
.\venv\Scripts\activate
python main.py
# Runs on: http://localhost:4201

# Terminal 2 - Atlas Frontend
cd c:\Users\mhkem\.atlas\frontend
npm run dev
# Runs on: http://localhost:4202

# Terminal 3 - Altimeter Backend (if needed)
# Runs on: http://localhost:4203

# Terminal 4 - Altimeter Frontend (if needed)
# Runs on: http://localhost:4204

# Access Points
# Atlas Frontend: http://localhost:4202
# Atlas Backend API: http://localhost:4201
# Atlas API Docs: http://localhost:4201/docs
# Altimeter Backend API: http://localhost:4203
# Altimeter Frontend: http://localhost:4204
```

### Production (Future)

- Deploy backend to cloud service (AWS/Azure/GCP)
- Deploy frontend to CDN
- Setup domain & SSL
- Configure reverse proxy for multi-system routing (Atlas: 4201/4202, Altimeter: 4203/4204)
- Enable monitoring & logging

---

## 6. SECURITY

### Credentials Management

```json
// config/secrets.json (encrypted at rest)
{
  "gmail": {
    "email": "your.email@gmail.com",
    "app_password": "encrypted_password"
  },
  "google_api": {
    "api_key": "encrypted_key"
  },
  "altimeter": {
    "database_path": "c:/Users/mhkem/.altimeter/database/altimeter.db",
    "api_key": "encrypted_key"
  }
}
```

### Authentication

- JWT tokens for API access
- Session management
- OAuth for Google services
- API key rotation

---

## 7. DATA RETENTION & PRIVACY

### Email Retention

- **Active**: Last 2 years in live database
- **Archive**: 2+ years in compressed archives
- **Deletion**: User-initiated only (never auto-delete)

### Privacy

- All data stored locally (not cloud)
- Gemini API: Only sends prompts, no storage
- Email credentials: Encrypted at rest
- Access logs for audit

---

## SUCCESS METRICS

- [ ] Email sync completes in <30 seconds
- [ ] Draft generation in <5 seconds
- [ ] Calendar conflicts detected automatically
- [ ] 90% of AI draft suggestions accepted
- [ ] Email zero inbox achieved
- [ ] Task completion rate increases 50%
- [ ] Time saved: 2+ hours/day

---

**Document Version**: 2.0  
**Last Updated**: 2026-01-18  
**Status**: Production-ready architecture
