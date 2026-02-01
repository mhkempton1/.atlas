# ATLAS SYSTEM CONTEXT FOR IDE LLM

## CRITICAL UNDERSTANDING

You are working within a **multi-system environment** for construction project management:

### 1. **Atlas** - AI-Powered Personal Assistant

**Location**: `C:\Users\mhkem\.atlas\`
**Purpose**: Unified gateway for email intelligence, calendar, tasks, AI agents, document control
**Tech Stack**: FastAPI (backend) + React/Vite (frontend) + SQLite + ChromaDB + Gemini AI
**Ports**:

- Backend: `http://localhost:4201` (FastAPI with OpenAPI docs at `/docs`)
- Frontend: `http://localhost:4202` (React + Vite)

### 2. **Altimeter** - Construction Project Management System

**Location**: `C:\Users\mhkem\.altimeter\`
**Purpose**: Work context provider - projects, customers, vendors, cost codes, scheduling, daily logs
**Database**: SQLite at `C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db`
**Ports**:

- Backend: `http://localhost:4203`
- Frontend: `http://localhost:4204`

### 3. **Davis Projects Knowledge Base**

**Location**: `C:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive\`
**Purpose**: Construction knowledge repository, templates, guidelines, cost codes, project files
**Structure**:

- `COST_CODES/` - Electrical cost code breakdowns (600-series)
- `GUIDELINES/` - Company procedures and SOPs
- `SKILLS/` - Domain expertise documentation (RFIs, submittals, estimating)
- `PROJECTS/` - Active project contexts and chat history
- `TEMPLATES/` - Reusable document templates
- `TRAINING/` - Training materials

---

## PORT ARCHITECTURE (UPDATED - CRITICAL)

**OLD PORTS (DEPRECATED)**: ~~6900, 5173, 5000~~

**NEW PORTS (ACTIVE)**:

- **Atlas Backend**: Port 4201
- **Atlas Frontend**: Port 4202
- **Altimeter Backend**: Port 4203
- **Altimeter Frontend**: Port 4204

### Updated Files with New Ports

- ✅ `backend/main.py` - Port 4201
- ✅ `frontend/vite.config.js` - Port 4202
- ✅ `backend/core/config.py` - CORS origins updated
- ✅ `frontend/src/services/api.js` - API_URL updated to 4201
- ✅ `ARCHITECTURE.md` - All references updated

---

## DATA FLOW & INTEGRATION

```
Gmail API → Atlas Email Service → AI Categorization (Gemini) → Project Linking (Altimeter)
    ↓                                                                      ↓
Draft Agent ← Project Context ←─────────────────────────── Altimeter DB Query
    ↓                                                                      ↓
Task Extraction → Task Agent → Priority/Effort Estimation ← Vector Search (ChromaDB)
    ↓                                                                      ↓
Calendar Agent → Google Calendar API ← Meeting Detection ← Email Analysis
    ↓                                                                      ↓
Document Control ← OneDrive Sync ←──────────────────────── Knowledge Base
```

### Bidirectional Sync

1. **Email → Altimeter**: Emails with project numbers auto-link to projects
2. **Altimeter → Atlas**: Project milestones create calendar events
3. **Tasks ↔ Projects**: Tasks linked to project IDs for context
4. **Files ↔ OneDrive**: Attachments and documents indexed for search

---

## KEY PRINCIPLES WHEN WORKING IN THIS ENVIRONMENT

### 1. **NEVER Truncate Email Bodies**

- CRITICAL requirement from ARCHITECTURE.md (lines 274-308)
- Store full `body_text` and `body_html` fields
- Archive old emails (2+ years) to compressed `.zip`, keep database records
- On-demand retrieval from archives

### 2. **Project Context is King**

- Always attempt to link emails/tasks/files to Altimeter `project_id`
- Format: `YY-NNNN` (e.g., `25-0308`, `25-0319`)
- Auto-detection: Regex search in subject/body, sender matching against Altimeter contacts

### 3. **Local-First Privacy**

- All data stored locally (SQLite + ChromaDB)
- No cloud storage except Google API calls (Gmail, Calendar)
- Gemini API receives only prompts, never stores data
- Credentials encrypted at rest in `config/secrets.json`

### 4. **Construction Domain Knowledge**

- **RFI** (Request for Information): Clarification questions to architect/engineer
- **Submittal**: Product data sheets for approval before purchase
- **Cost Codes**: 600-series for electrical work (e.g., 621 = Homeruns)
- **Daily Logs**: Job site activity tracking
- **Change Orders**: Scope/budget modifications

### 5. **AI-Powered Intelligence**

- **Gemini 2.0 Flash**: Email drafting, categorization, task extraction, Q&A
- **ChromaDB Vector Search**: Semantic search across emails/files (RAG)
- **Ollama Fallback**: Local models if cloud API unavailable

---

## FILE STRUCTURE & LOCATIONS

### Atlas Backend (`C:\Users\mhkem\.atlas\backend\`)

```
backend/
├── agents/           # AI agents (draft, task, calendar, project)
│   ├── draft_agent.py
│   ├── task_agent.py
│   └── base.py
├── api/              # REST endpoints
│   ├── routes.py     # Main router
│   ├── email_routes.py
│   └── system_routes.py
├── core/             # App core
│   ├── app.py        # FastAPI application
│   └── config.py     # Settings (CORS, paths, API keys)
├── database/         # Database models (SQLAlchemy)
│   └── models.py     # Email, Task, Contact, CalendarEvent, etc.
├── services/         # Business logic
│   ├── gmail_service.py
│   ├── altimeter_service.py
│   ├── ai_service.py
│   ├── knowledge_service.py
│   ├── document_control_service.py
│   └── search_service.py (ChromaDB)
└── main.py           # Entry point (runs on port 4201)
```

### Atlas Frontend (`C:\Users\mhkem\.atlas\frontend\src\`)

```
frontend/src/
├── components/
│   ├── email/        # Email intelligence UI
│   │   ├── EmailList.jsx
│   │   ├── EmailView.jsx
│   │   ├── ComposeDraft.jsx
│   │   └── ThreadView.jsx
│   ├── tasks/        # Task management UI
│   │   ├── TaskList.jsx
│   │   ├── TaskBoard.jsx (Kanban)
│   │   └── TaskDetail.jsx
│   ├── calendar/     # Calendar UI
│   │   ├── CalendarView.jsx
│   │   ├── EventDetail.jsx
│   │   └── MeetingScheduler.jsx
│   ├── dashboard/    # Command center
│   │   ├── Dashboard.jsx
│   │   └── SystemHealthView.jsx
│   └── documents/    # Document control
│       └── DocumentControl.jsx
├── services/
│   └── api.js        # Axios API client (base URL: localhost:4201)
├── App.jsx           # Main app with navigation
└── main.jsx          # Entry point
```

### Data Storage (`C:\Users\mhkem\.atlas\data\`)

```
data/
├── databases/
│   ├── atlas.db      # SQLite database
│   └── vectors/      # ChromaDB persistent storage
├── files/
│   └── attachments/  # Email attachments
└── logs/             # System logs
```

---

## DATABASE SCHEMA (SQLAlchemy Models)

### Critical Tables

- **emails**: Full email storage (gmail_id, from, to, subject, body_text, body_html, project_id, raw_eml BLOB)
- **email_attachments**: File metadata and paths
- **email_threads**: Conversation grouping
- **drafts**: AI-generated drafts with metadata
- **contacts**: Unified contacts (linked to Altimeter customers/vendors)
- **tasks**: Task management (linked to emails, projects)
- **calendar_events**: Google Calendar sync
- **files**: File metadata with vector embeddings

**Foreign Keys**:

- `emails.project_id` → Altimeter `Projects.ProjectID`
- `contacts.altimeter_customer_id` → Altimeter `Customers.CustomerID`
- `tasks.email_id` → `emails.email_id`

**Indexes**: gmail_id, thread_id, project_id, date_received, email_address

---

## API ENDPOINTS (Backend)

### Current Endpoints (Existing)

- `GET /` - System status
- `GET /health` - Health check
- `POST /api/v1/agents/draft` - Generate email draft
- `POST /api/v1/agents/send-email` - Send email via Gmail
- `GET /api/v1/knowledge/docs` - List knowledge documents
- `GET /api/v1/knowledge/content` - Get document content
- `GET /api/v1/docs/list` - List controlled documents
- `POST /api/v1/docs/promote-review` - Promote document to review
- `POST /api/v1/docs/lock` - Lock document
- `GET /api/v1/dashboard/status` - System health (proxies Altimeter)
- `GET /api/v1/dashboard/schedule` - Employee schedule (from Altimeter)

### Needed Endpoints (To Implement)

See `IDE_LLM_BUILD_PROMPT.md` Phase 4.6 for full list of required endpoints:

- Email CRUD: `/api/v1/email/*`
- Task CRUD: `/api/v1/tasks/*`
- Calendar CRUD: `/api/v1/calendar/*`
- AI assistant: `/api/v1/ai/*`
- Settings: `/api/v1/settings/*`

---

## INTEGRATION PATTERNS

### 1. Email → Project Linking

```python
# In gmail_service.py after fetching email
email = fetch_email_from_gmail(message_id)
email.project_id = altimeter_service.link_email_to_project(email)
if email.project_id:
    email.category = 'work'
    project_context = altimeter_service.get_project_context(email.project_id)
```

### 2. Draft Generation with Context

```python
# In draft_agent.py
def generate_draft(email, instructions):
    context = {}
    if email.project_id:
        context = altimeter_service.get_project_context(email.project_id)

    prompt = f"""
    Original Email: {email.subject}
    From: {email.from_address}

    Project Context: {context}

    Generate a professional reply...
    """
    return gemini.generate_content(prompt)
```

### 3. Vector Search (RAG)

```python
# In search_service.py
def search_emails(query, project_id=None):
    filters = {'project_id': project_id} if project_id else None
    results = chroma_collection.query(
        query_texts=[query],
        n_results=10,
        where=filters
    )
    return results
```

---

## CURRENT SYSTEM STATE

### ✅ Implemented

- Basic FastAPI backend structure
- React frontend with navigation
- Draft agent with Gemini integration
- Gmail send functionality
- Knowledge base document reading
- Document control workflow
- Dashboard with system health
- Altimeter connector (basic)

### ❌ Not Implemented (See Build Prompt)

- Email inbox UI and sync
- Task management (extraction, UI, Kanban)
- Calendar integration
- Vector search with ChromaDB
- Background scheduler
- Most AI agents (task, calendar, project)
- Settings UI
- Full API endpoints

---

## WHEN HELPING WITH CODE/TASKS

### 1. **Check Integration Points**

- Does this affect Atlas ↔ Altimeter sync?
- Does this require Gemini API calls?
- Does this need vector search?

### 2. **Respect Data Schemas**

- Follow SQLAlchemy models (when implemented)
- Match ARCHITECTURE.md schema (lines 120-272)
- Never truncate email bodies

### 3. **Use Existing Services**

- Import from `services/` modules
- Don't recreate functionality
- Check `api/routes.py` for existing endpoints

### 4. **Test with Real Data**

- Active projects: 25-0308, 25-0319, 25-0465
- Use actual Gmail account for testing
- Query Altimeter DB for real project data

### 5. **Construction Context**

- Reference `GUIDELINES/` for procedures
- Use `COST_CODES/` for electrical work breakdown
- Check `SKILLS/` for domain expertise

---

## COMMON TASKS & SOLUTIONS

### Task: Add new API endpoint

**Steps**:

1. Create Pydantic request/response models
2. Add route function in appropriate `*_routes.py`
3. Include router in `api/routes.py` (if new file)
4. Add corresponding function in `services/api.js` (frontend)
5. Test with `/docs` OpenAPI interface

### Task: Implement AI agent

**Steps**:

1. Create agent class in `agents/` inheriting from `base.py`
2. Implement `process(context)` method
3. Call Gemini API with constructed prompt
4. Return structured result (dict/Pydantic model)
5. Create API endpoint to expose agent
6. Test with real data

### Task: Add frontend component

**Steps**:

1. Create `.jsx` file in appropriate `components/` subfolder
2. Import required icons from `lucide-react`
3. Use Tailwind CSS for styling
4. Import API functions from `services/api.js`
5. Add to navigation in `App.jsx`
6. Test in browser at `localhost:4202`

### Task: Query Altimeter database

**Steps**:

1. Use `altimeter_service.py` functions
2. Import SQLite connection from service
3. Query Altimeter schema (Projects, Customers, DailyLogs, etc.)
4. Map results to Atlas data structures
5. Cache frequently accessed data

---

## TROUBLESHOOTING

### Backend won't start

- Check virtual environment activated: `.venv\Scripts\activate`
- Verify port 4201 not in use: `netstat -ano | findstr 4201`
- Check logs in `data/logs/`
- Verify `config/secrets.json` exists

### Frontend API calls fail

- Verify backend running on port 4201
- Check CORS origins in `backend/core/config.py`
- Inspect browser console for errors
- Test endpoint directly at `localhost:4201/docs`

### Altimeter connection fails

- Verify Altimeter database path: `C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db`
- Check file permissions
- Test with SQLite browser tool

### Gemini API errors

- Verify `GEMINI_API_KEY` in `config/secrets.json`
- Check API quota/rate limits
- Fallback to Ollama if cloud fails

---

## SECURITY CONSTRAINTS

- **Never expose** `config/secrets.json` contents
- **Never commit** API keys to git (use `.gitignore`)
- **Encrypt credentials** at rest (implement in config.py)
- **Validate inputs** to prevent SQL injection/XSS
- **Use JWT tokens** for API authentication (future)
- **HTTPS only** in production

---

## TESTING STRATEGY

### Unit Tests (`backend/tests/`)

- Test individual functions with mocks
- Run with `pytest -v`

### Integration Tests

- Test full workflows (email sync → task extraction → draft)
- Use test database (not production)

### Frontend Tests (`frontend/src/components/__tests__/`)

- Vitest + React Testing Library
- Test component rendering, user interactions
- Run with `npm test`

### Manual Testing Checklist

- [ ] Email sync from Gmail
- [ ] Project linking works
- [ ] Draft generation includes context
- [ ] Tasks extract from emails
- [ ] Calendar syncs from Google
- [ ] Vector search returns relevant results
- [ ] Dashboard displays accurate data
- [ ] All API calls succeed (check Network tab)

---

## QUICK START COMMANDS

### Start Atlas Backend

```bash
cd C:\Users\mhkem\.atlas\backend
.venv\Scripts\activate
python main.py
# Access at: http://localhost:4201
# API Docs at: http://localhost:4201/docs
```

### Start Atlas Frontend

```bash
cd C:\Users\mhkem\.atlas\frontend
npm run dev
# Access at: http://localhost:4202
```

### Query Altimeter Database

```bash
sqlite3 "C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db"
.tables
SELECT * FROM Projects WHERE ProjectID LIKE '25-%';
```

### Run Tests

```bash
# Backend
cd C:\Users\mhkem\.atlas\backend
pytest -v

# Frontend
cd C:\Users\mhkem\.atlas\frontend
npm test
```

---

## REFERENCE DOCUMENTS

- **Architecture Spec**: `C:\Users\mhkem\.atlas\ARCHITECTURE.md` (full system design)
- **Build Prompt**: `C:\Users\mhkem\.atlas\IDE_LLM_BUILD_PROMPT.md` (detailed task list)
- **Davis Projects**: `C:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive\` (knowledge base)

---

## TL;DR FOR QUICK CONTEXT

**What is Atlas?** AI assistant for construction PM - email intelligence + calendar + tasks + AI agents

**What is Altimeter?** Construction project management database with projects, customers, budgets, schedules

**How do they connect?** Emails auto-link to projects, tasks sync, shared context for AI

**Key Ports**: Atlas BE=4201, Atlas FE=4202, Altimeter BE=4203, Altimeter FE=4204

**Key Rule**: NEVER truncate email bodies, always link to Altimeter projects when possible

**Tech Stack**: FastAPI + React + SQLite + ChromaDB + Gemini AI

**Current State**: Basic structure exists, need to implement full email/task/calendar workflows (see build prompt)

---

**Use this context when working on Atlas code. Always check integration points with Altimeter and respect the construction domain knowledge.**
