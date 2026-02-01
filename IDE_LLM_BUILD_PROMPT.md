# ATLAS SYSTEM BUILD-OUT PROMPT FOR IDE LLM

## SYSTEM OVERVIEW

You are building out **Atlas**, a personal AI assistant platform for construction project management. Atlas integrates with **Altimeter** (construction PM system) and **Davis Projects Knowledge Base** (OneDrive).

### Port Architecture (CRITICAL - ALL UPDATED)

- **Atlas Backend**: `http://localhost:4201` (FastAPI)
- **Atlas Frontend**: `http://localhost:4202` (React + Vite)
- **Altimeter Backend**: `http://localhost:4203` (FastAPI)
- **Altimeter Frontend**: `http://localhost:4204` (React + Vite)

### Key Paths

- Atlas Root: `C:\Users\mhkem\.atlas\`
- Altimeter Root: `C:\Users\mhkem\.altimeter\`
- Knowledge Base: `C:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive\`
- Altimeter Database: `C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db`
- Atlas Database: `C:\Users\mhkem\OneDrive\Documents\databasedev\atlas.db`

---

## PRIORITY BUILD TASKS

### PHASE 1: CORE INFRASTRUCTURE (Foundation)

#### 1.1 Database Schema Implementation

**Location**: `C:\Users\mhkem\.atlas\backend\database\`

**Tasks**:

- [ ] Create `models.py` with SQLAlchemy models matching ARCHITECTURE.md schema (lines 120-272)
  - `Email` model with FULL body storage (NEVER truncate)
  - `EmailAttachment` model with file hash deduplication
  - `EmailThread` model with participant tracking
  - `Draft` model with AI generation metadata
  - `Contact` model with Altimeter linking (customer_id, vendor_id)
  - `Task` model with parent/subtask relationships
  - `CalendarEvent` model with Google Calendar sync fields
  - `File` model with vector embedding support
- [ ] Create `database.py` with SQLAlchemy engine and session management
- [ ] Create migration script `init_db.py` to bootstrap schema
- [ ] Add indexes for performance:
  - `emails.gmail_id` (unique)
  - `emails.thread_id` (lookup)
  - `emails.project_id` (Altimeter linking)
  - `emails.date_received` (time-based queries)
  - `contacts.email_address` (unique)
  - `tasks.project_id` (project filtering)

**Validation**: Run `init_db.py`, verify all tables created with `sqlite3 atlas.db .schema`

---

#### 1.2 Gmail Service Integration

**Location**: `C:\Users\mhkem\.atlas\backend\services\gmail_service.py`

**Current State**: Basic send_email exists, needs full CRUD

**Tasks**:

- [ ] Implement OAuth 2.0 authentication flow with Google
  - Store credentials in `config/secrets.json` (encrypted)
  - Refresh token handling
- [ ] `sync_emails(last_sync_timestamp)` - Fetch new emails since last sync
  - Use Gmail API with `after:TIMESTAMP` query
  - Parse full email body (text + HTML)
  - Download attachments to `data/files/attachments/{email_id}/`
  - Store raw EML in `raw_eml` BLOB field
  - Extract metadata: labels, importance, recipients
- [ ] `categorize_email(email)` - AI categorization
  - Call Gemini API to classify: work/personal/urgent/spam/promotional
  - Auto-link to Altimeter project if project number detected in subject/body
  - Match sender against Altimeter contacts database
- [ ] `get_email_by_id(email_id)` - Retrieve full email with attachments
- [ ] `get_emails_by_thread(thread_id)` - Get conversation thread
- [ ] `mark_as_read(email_id)` / `mark_as_starred(email_id)`
- [ ] `archive_old_emails()` - Compress emails older than 2 years to `.zip`
  - Keep database record with `archive_path` reference
  - Clear `raw_eml` BLOB from active database

**Integration**: Must call `altimeter_service.link_email_to_project(email)` after categorization

**Validation**: Sync 10 test emails, verify full body storage, check Altimeter project linking

---

#### 1.3 Altimeter Integration Service

**Location**: `C:\Users\mhkem\.atlas\backend\services\altimeter_service.py`

**Current State**: Basic connector exists, needs full integration

**Tasks**:

- [ ] `connect_to_altimeter_db()` - Open SQLite connection to Altimeter database
- [ ] `link_email_to_project(email)` - Auto-link emails to projects
  - Regex search for project numbers (format: `YY-NNNN` like `25-0308`)
  - Query Altimeter `Contacts` table to match sender email
  - Query Altimeter `Projects` table for active projects with matching contact
  - Update `email.project_id` and `email.category = 'work'`
- [ ] `get_project_context(project_id)` - Return project details for AI
  - Project name, status, budget, schedule
  - Recent daily logs (last 5 entries)
  - Open RFIs, pending submittals
  - Upcoming deliveries
- [ ] `get_contact_by_email(email_address)` - Find Altimeter contact
  - Return customer/vendor details
  - Link to `contacts` table in Atlas
- [ ] `get_active_projects()` - List all active projects for dropdown
- [ ] `sync_project_milestones_to_calendar()` - Create calendar events from Altimeter schedule

**Validation**: Test with real project `25-0308`, verify email linking and context retrieval

---

### PHASE 2: AI AGENTS (Intelligence Layer)

#### 2.1 Draft Agent Enhancement

**Location**: `C:\Users\mhkem\.atlas\backend\agents\draft_agent.py`

**Current State**: Basic draft generation exists

**Tasks**:

- [ ] Enhance context awareness:
  - If `email.project_id` exists, fetch project context from Altimeter
  - Include recent project activity in prompt
  - Reference cost codes if discussing budget/materials
- [ ] Support multiple draft variations:
  - Generate 3 tone variations: formal, casual, brief
  - Allow user to select preferred draft
- [ ] Draft review workflow:
  - Save draft to `drafts` table with status='draft'
  - Frontend review UI before sending
  - Track AI model used and generation prompt
- [ ] Fallback to Ollama if Gemini API unavailable:
  - Check API key validity
  - Try local Llama model if cloud fails
- [ ] Handle reply threading:
  - Detect if email is a reply (check `In-Reply-To` header)
  - Include conversation history in prompt

**Validation**: Generate draft for project email, verify project context included

---

#### 2.2 Task Agent Implementation

**Location**: `C:\Users\mhkem\.atlas\backend\agents\task_agent.py`

**Current State**: Basic structure exists, needs full implementation

**Tasks**:

- [ ] `extract_tasks_from_email(email)` - AI extraction of action items
  - Parse email body with Gemini API
  - Identify: task description, priority, due date (if mentioned)
  - Return JSON array of tasks
- [ ] `prioritize_tasks(task_list)` - AI prioritization
  - Consider: due date, project status, dependencies
  - Assign high/medium/low priority
- [ ] `suggest_task_breakdown(task)` - Break complex tasks into subtasks
  - If estimated_hours > 8, suggest breakdown
  - Create parent-child task relationships
- [ ] `estimate_effort(task)` - AI effort estimation
  - Based on task description and historical data
  - Return estimated hours
- [ ] `detect_dependencies(task_list)` - Find task dependencies
  - Identify tasks that must complete before others
  - Flag blockers

**Integration**: Auto-create tasks after email sync, link to `email.email_id`

**Validation**: Process email with multiple action items, verify task extraction

---

#### 2.3 Calendar Agent Implementation

**Location**: `C:\Users\mhkem\.atlas\backend\agents\calendar_agent.py`

**Current State**: Not implemented

**Tasks**:

- [ ] `sync_google_calendar()` - Fetch calendar events
  - OAuth 2.0 with Google Calendar API
  - Sync both work and personal calendars
  - Store in `calendar_events` table
- [ ] `detect_conflicts(new_event)` - Check for overlapping events
  - Query existing events by time range
  - Return list of conflicts
- [ ] `suggest_meeting_times(duration, attendees, date_range)` - AI scheduling
  - Find free slots in all attendees' calendars
  - Prefer morning slots for important meetings
  - Avoid back-to-back meetings (add buffer time)
- [ ] `extract_meeting_from_email(email)` - Detect meeting requests
  - Parse email for date/time mentions
  - Extract attendees from body
  - Auto-create draft calendar event
- [ ] `prepare_meeting_context(event_id)` - Gather related info
  - Find related emails (by subject/attendees)
  - Find related project files
  - Summarize recent project activity

**Integration**: Link events to Altimeter projects via `project_id`

**Validation**: Sync calendar, detect conflicts, suggest meeting times

---

#### 2.4 Project Agent Implementation

**Location**: `C:\Users\mhkem\.atlas\backend\agents\project_agent.py`

**Current State**: Not implemented

**Tasks**:

- [ ] `get_project_summary(project_id)` - AI-generated project overview
  - Combine Altimeter data with email history
  - Summarize recent activity, status, issues
- [ ] `suggest_next_actions(project_id)` - AI recommendations
  - Based on project phase, open items, schedule
  - Prioritize by urgency and impact
- [ ] `detect_project_risks(project_id)` - Risk analysis
  - Overdue invoices
  - Pending RFIs/submittals blocking work
  - Schedule delays
  - Budget overruns
- [ ] `answer_project_question(project_id, question)` - RAG-powered Q&A
  - Search vector database for relevant emails/files
  - Query Altimeter for structured data
  - Generate answer with citations

**Integration**: Primary interface for project-specific AI assistance

**Validation**: Ask "What's the status of project 25-0308?" and get comprehensive answer

---

### PHASE 3: VECTOR SEARCH & RAG (Knowledge Layer)

#### 3.1 ChromaDB Setup

**Location**: `C:\Users\mhkem\.atlas\backend\services\search_service.py`

**Tasks**:

- [ ] Initialize ChromaDB persistent client
  - Storage path: `data/databases/vectors/`
  - Create collections: `emails`, `files`, `documents`
- [ ] `index_email(email)` - Add email to vector store
  - Combine subject + body for embedding
  - Store metadata: email_id, from, date, project_id
  - Use sentence-transformers or OpenAI embeddings
- [ ] `index_file(file)` - Add file to vector store
  - Extract text from PDFs, DOCX, TXT
  - Chunk large documents (500 word chunks)
  - Store metadata: file_id, filename, project_id
- [ ] `search_emails(query, filters)` - Semantic search
  - Natural language queries
  - Filter by project_id, date_range, sender
  - Return top 10 results with relevance scores
- [ ] `search_files(query, filters)` - File search
  - Search across email attachments and OneDrive files
  - Support filters by file type, project
- [ ] Background indexing job:
  - Run hourly to index new emails/files
  - Update embeddings if content changes

**Validation**: Search "What did John say about the electrical submittal?" and retrieve relevant emails

---

### PHASE 4: FRONTEND IMPLEMENTATION (User Interface)

#### 4.1 Email Intelligence Module

**Location**: `C:\Users\mhkem\.atlas\frontend\src\components\email\`

**Current State**: Basic `ComposeDraft` exists, needs full inbox

**Tasks**:

- [ ] `EmailList.jsx` - Inbox view component
  - List emails with: sender, subject, snippet, date, labels
  - Color coding by category (work=blue, urgent=red, personal=green)
  - Filter by: unread, starred, project, date range
  - Sort by: date, importance, sender
  - Pagination (50 emails per page)
  - Search bar with autocomplete
- [ ] `EmailView.jsx` - Full email display component
  - Display: from, to, cc, subject, full body (HTML rendering)
  - Show attachments with download links
  - Show project link if `project_id` exists (clickable to Altimeter)
  - Action buttons: Reply, Forward, Star, Archive, Delete
  - "Generate Draft Reply" button (calls draft agent)
- [ ] `ThreadView.jsx` - Conversation thread display
  - Group emails by `thread_id`
  - Chronological order
  - Collapse older messages
  - Unified reply at bottom
- [ ] `EmailFilters.jsx` - Filter sidebar
  - Checkboxes: Unread, Starred, Has Attachments
  - Dropdown: Category, Project, Sender
  - Date range picker
- [ ] `ComposeDraft.jsx` - Enhance existing component
  - Add recipient autocomplete from contacts
  - Rich text editor (bold, italic, lists, links)
  - Attachment upload (drag & drop)
  - Save as draft functionality
  - Send button with loading state

**API Integration**: Connect to `/api/v1/email/*` endpoints (need to create these in Phase 4.6)

**Validation**: View inbox, read email, generate draft reply, send email

---

#### 4.2 Task Management Module

**Location**: `C:\Users\mhkem\.atlas\frontend\src\components\tasks\`

**Current State**: Not implemented

**Tasks**:

- [ ] `TaskList.jsx` - List view component
  - Display tasks with: title, priority, due date, status, project
  - Filter by: status (todo/in_progress/done/blocked), priority, project
  - Sort by: due date, priority, created date
  - Checkbox to mark complete
  - Click to expand for details
- [ ] `TaskBoard.jsx` - Kanban board view
  - Columns: To Do, In Progress, Done, Blocked
  - Drag & drop to change status
  - Color coding by priority (high=red, medium=yellow, low=green)
  - Swimlanes by project (optional)
- [ ] `TaskDetail.jsx` - Task detail modal
  - Edit: title, description, priority, due date, estimated hours
  - Link to source email (if `email_id` exists)
  - Link to project (if `project_id` exists)
  - Subtask list (if parent task)
  - Comments/notes
  - Track actual hours
- [ ] `TaskCreate.jsx` - Create task form
  - Manual task creation
  - Auto-populate from email (if triggered from email)
  - Project dropdown (from Altimeter)
  - AI suggestion for priority/effort

**API Integration**: Create `/api/v1/tasks/*` endpoints in backend

**Validation**: Create task, view Kanban board, mark complete, link to email

---

#### 4.3 Calendar Module

**Location**: `C:\Users\mhkem\.atlas\frontend\src\components\calendar\`

**Current State**: Basic `SchedulerView` exists, needs full calendar

**Tasks**:

- [ ] `CalendarView.jsx` - Month/week/day calendar views
  - Month view: grid with event dots
  - Week view: time slots with event blocks
  - Day view: hourly breakdown
  - Toggle between work/personal calendars
  - Color coding by calendar source
- [ ] `EventDetail.jsx` - Event detail modal
  - Display: title, description, location, start/end time, attendees
  - Link to project if `project_id` exists
  - "Meeting Prep" button (calls project agent for context)
  - Edit/Delete buttons
  - Join meeting link (if virtual)
- [ ] `MeetingScheduler.jsx` - Smart scheduling component
  - Select duration, attendees, date range
  - AI suggests optimal time slots
  - Show attendee availability (if accessible)
  - One-click create event
- [ ] `ConflictAlert.jsx` - Conflict notification component
  - Show overlapping events
  - Suggest resolution (reschedule, shorten, decline)

**API Integration**: Create `/api/v1/calendar/*` endpoints in backend

**Validation**: View calendar, create event, detect conflicts, schedule meeting

---

#### 4.4 Dashboard / Command Center

**Location**: `C:\Users\mhkem\.atlas\frontend\src\components\dashboard\`

**Current State**: Basic `Dashboard.jsx` exists, needs widgets

**Tasks**:

- [ ] `Dashboard.jsx` - Main dashboard layout
  - Grid layout with draggable widgets
  - Widget types: Email Summary, Task Summary, Calendar, Project Status, AI Assistant
  - Persist widget positions in localStorage
- [ ] `EmailSummaryWidget.jsx` - Email stats
  - Unread count
  - Urgent emails (red badge)
  - Recent emails (last 5)
  - "View Inbox" button
- [ ] `TaskSummaryWidget.jsx` - Task stats
  - Tasks by status (pie chart)
  - Overdue tasks (red list)
  - Today's tasks
  - "View Tasks" button
- [ ] `CalendarWidget.jsx` - Today's schedule
  - Next 3 upcoming events
  - Time until next meeting
  - "View Calendar" button
- [ ] `ProjectStatusWidget.jsx` - Active projects
  - List active Altimeter projects
  - Status indicators (on-track, at-risk, delayed)
  - Recent activity summary
  - Click to view project details
- [ ] `AIAssistantWidget.jsx` - Chat interface
  - Text input for natural language queries
  - Display AI responses
  - Quick actions: "Summarize unread emails", "What's my schedule today?", "Show urgent tasks"
  - Chat history (last 10 messages)

**API Integration**: Create `/api/v1/dashboard/*` endpoints for aggregated data

**Validation**: Dashboard loads with all widgets, displays accurate data, AI assistant responds

---

#### 4.5 Settings / Configuration Module

**Location**: `C:\Users\mhkem\.atlas\frontend\src\components\settings\`

**Current State**: Placeholder in App.jsx

**Tasks**:

- [ ] `Settings.jsx` - Main settings page
  - Tabs: Account, Integrations, Notifications, Appearance, System
- [ ] `AccountSettings.jsx` - User profile
  - Name, email, role, strata level
  - Change password
  - Session management
- [ ] `IntegrationSettings.jsx` - External connections
  - Gmail: Connect/disconnect, last sync time, sync now button
  - Google Calendar: Connect/disconnect, calendar selection
  - Altimeter: Database path, connection status, sync status
  - OneDrive: Path, sync status
- [ ] `NotificationSettings.jsx` - Notification preferences
  - Email notifications: urgent emails, task due dates, calendar reminders
  - Desktop notifications toggle
  - Notification sound toggle
- [ ] `AppearanceSettings.jsx` - UI customization
  - Theme: Dark/Light/Auto
  - Font size: Small/Medium/Large
  - Sidebar position: Left/Right
- [ ] `SystemSettings.jsx` - Advanced configuration (Strata 4+ only)
  - API keys (Gemini, OpenAI)
  - Database maintenance: vacuum, backup, restore
  - Log level: Debug/Info/Warning/Error
  - Clear cache

**API Integration**: Create `/api/v1/settings/*` endpoints in backend

**Validation**: Change settings, verify persistence across sessions

---

#### 4.6 Backend API Routes (Supporting Frontend)

**Location**: `C:\Users\mhkem\.atlas\backend\api\`

**Current State**: Basic routes in `routes.py`, needs expansion

**Tasks**:

- [ ] `email_routes.py` - Email endpoints
  - `GET /api/v1/email/list` - Get emails with filters
  - `GET /api/v1/email/{email_id}` - Get single email
  - `GET /api/v1/email/thread/{thread_id}` - Get thread
  - `POST /api/v1/email/send` - Send email (already exists, enhance)
  - `POST /api/v1/email/sync` - Trigger email sync
  - `PUT /api/v1/email/{email_id}/read` - Mark as read
  - `PUT /api/v1/email/{email_id}/star` - Toggle star
  - `DELETE /api/v1/email/{email_id}` - Archive email
- [ ] `task_routes.py` - Task endpoints
  - `GET /api/v1/tasks/list` - Get tasks with filters
  - `GET /api/v1/tasks/{task_id}` - Get single task
  - `POST /api/v1/tasks/create` - Create task
  - `PUT /api/v1/tasks/{task_id}` - Update task
  - `DELETE /api/v1/tasks/{task_id}` - Delete task
  - `POST /api/v1/tasks/extract` - Extract tasks from email
- [ ] `calendar_routes.py` - Calendar endpoints
  - `GET /api/v1/calendar/events` - Get events with filters
  - `GET /api/v1/calendar/{event_id}` - Get single event
  - `POST /api/v1/calendar/sync` - Trigger calendar sync
  - `POST /api/v1/calendar/create` - Create event
  - `PUT /api/v1/calendar/{event_id}` - Update event
  - `DELETE /api/v1/calendar/{event_id}` - Delete event
  - `POST /api/v1/calendar/suggest-times` - AI meeting scheduler
- [ ] `dashboard_routes.py` - Dashboard endpoints (enhance existing)
  - `GET /api/v1/dashboard/summary` - Aggregated dashboard data
  - `GET /api/v1/dashboard/email-stats` - Email statistics
  - `GET /api/v1/dashboard/task-stats` - Task statistics
  - `GET /api/v1/dashboard/upcoming-events` - Next 5 events
  - `GET /api/v1/dashboard/project-status` - Active projects summary
- [ ] `ai_routes.py` - AI assistant endpoints
  - `POST /api/v1/ai/chat` - Chat with AI assistant
  - `POST /api/v1/ai/search` - Semantic search
  - `POST /api/v1/ai/summarize` - Summarize email/thread
  - `POST /api/v1/ai/project-question` - Ask about project
- [ ] `settings_routes.py` - Settings endpoints
  - `GET /api/v1/settings/user` - Get user settings
  - `PUT /api/v1/settings/user` - Update user settings
  - `GET /api/v1/settings/integrations` - Get integration status
  - `POST /api/v1/settings/integrations/sync` - Trigger sync
  - `POST /api/v1/settings/system/backup` - Create database backup

**Validation**: Test all endpoints with Postman/Thunder Client, verify CORS headers

---

### PHASE 5: BACKGROUND JOBS & AUTOMATION

#### 5.1 Scheduler Service

**Location**: `C:\Users\mhkem\.atlas\backend\services\scheduler_service.py`

**Current State**: Basic structure exists

**Tasks**:

- [ ] Setup APScheduler for background jobs
- [ ] `schedule_email_sync()` - Run every 5 minutes
  - Call `gmail_service.sync_emails()`
  - Index new emails in ChromaDB
  - Trigger task extraction for new emails
- [ ] `schedule_calendar_sync()` - Run every 15 minutes
  - Call `calendar_agent.sync_google_calendar()`
- [ ] `schedule_daily_digest()` - Run at 7:00 AM daily
  - Generate email summary of yesterday's activity
  - List today's tasks and meetings
  - Send as email or push notification
- [ ] `schedule_project_alerts()` - Run every hour
  - Check for overdue RFIs, submittals
  - Check for upcoming deadlines (next 48 hours)
  - Send alerts for critical items
- [ ] `schedule_archive_old_emails()` - Run monthly
  - Compress emails older than 2 years
  - Update database records with archive paths
- [ ] `schedule_database_maintenance()` - Run weekly
  - SQLite VACUUM
  - Backup database to `data/backups/`
  - Rotate logs (keep last 30 days)

**Validation**: Verify jobs run on schedule, check logs for errors

---

### PHASE 6: TESTING & VALIDATION

#### 6.1 Backend Unit Tests

**Location**: `C:\Users\mhkem\.atlas\backend\tests\`

**Tasks**:

- [ ] `test_gmail_service.py` - Gmail service tests
  - Mock Gmail API responses
  - Test email sync, categorization, linking
- [ ] `test_altimeter_service.py` - Altimeter integration tests
  - Test project linking, context retrieval
- [ ] `test_draft_agent.py` - Draft agent tests
  - Mock Gemini API
  - Test context injection, tone variations
- [ ] `test_task_agent.py` - Task agent tests
  - Test task extraction, prioritization
- [ ] `test_search_service.py` - Vector search tests
  - Test indexing, semantic search, filters
- [ ] Run with: `pytest backend/tests/ -v`

---

#### 6.2 Frontend Component Tests

**Location**: `C:\Users\mhkem\.atlas\frontend\src\components\__tests__\`

**Tasks**:

- [ ] Setup Vitest + React Testing Library
- [ ] Test critical components:
  - `EmailList.test.jsx` - Email list rendering, filtering
  - `TaskBoard.test.jsx` - Task drag & drop
  - `Dashboard.test.jsx` - Widget rendering
- [ ] Run with: `npm test`

---

#### 6.3 Integration Tests

**Location**: `C:\Users\mhkem\.atlas\backend\tests\integration\`

**Tasks**:

- [ ] `test_email_workflow.py` - End-to-end email workflow
  - Sync email → Categorize → Link to project → Extract tasks → Generate draft reply
- [ ] `test_altimeter_sync.py` - Altimeter bidirectional sync
  - Email linked to project → Project context retrieved → Task created
- [ ] `test_ai_assistant.py` - AI assistant queries
  - Ask question → Vector search → Generate answer with citations

---

### PHASE 7: DOCUMENTATION & DEPLOYMENT

#### 7.1 API Documentation

**Tasks**:

- [ ] Enhance FastAPI OpenAPI docs with descriptions
- [ ] Add request/response examples
- [ ] Document authentication requirements
- [ ] Accessible at: `http://localhost:4201/docs`

---

#### 7.2 User Guide

**Location**: `C:\Users\mhkem\.atlas\docs\USER_GUIDE.md`

**Tasks**:

- [ ] Getting started guide
- [ ] Feature walkthroughs with screenshots
- [ ] Troubleshooting section
- [ ] FAQ

---

#### 7.3 Deployment Scripts

**Location**: `C:\Users\mhkem\.atlas\scripts\`

**Tasks**:

- [ ] `start_atlas.bat` - Start backend + frontend (Windows)
  - Terminal 1: `cd backend && .venv\Scripts\activate && python main.py`
  - Terminal 2: `cd frontend && npm run dev`
- [ ] `backup_database.py` - Manual database backup script
- [ ] `restore_database.py` - Restore from backup

---

## IMPLEMENTATION PRIORITIES

### CRITICAL PATH (Do First)

1. Database schema (1.1)
2. Gmail service (1.2)
3. Altimeter integration (1.3)
4. Draft agent (2.1)
5. Email list UI (4.1)
6. Backend email routes (4.6)

### HIGH PRIORITY (Do Second)

7. Task agent (2.2)
2. Task management UI (4.2)
3. Vector search (3.1)
4. Background scheduler (5.1)

### MEDIUM PRIORITY (Do Third)

11. Calendar agent (2.3)
2. Calendar UI (4.3)
3. Dashboard (4.4)
4. Settings (4.5)

### LOW PRIORITY (Polish)

15. Project agent (2.4)
2. Testing (6.1-6.3)
3. Documentation (7.1-7.3)

---

## VALIDATION CHECKLIST

After completing all phases, verify:

- [ ] Email sync works: Fetch 50+ emails from Gmail
- [ ] Emails auto-link to Altimeter projects (test with project 25-0308)
- [ ] Draft generation includes project context
- [ ] Tasks extract from emails automatically
- [ ] Vector search returns relevant results
- [ ] Calendar syncs from Google Calendar
- [ ] Dashboard displays accurate stats
- [ ] Background jobs run on schedule
- [ ] Frontend connects to backend (all API calls work)
- [ ] Settings persist across sessions
- [ ] No console errors in browser or terminal
- [ ] All ports configured correctly (4201/4202 for Atlas, 4203/4204 for Altimeter)

---

## CODING STANDARDS

### Backend (Python/FastAPI)

- Use type hints for all function signatures
- Async/await for I/O operations
- Pydantic models for request/response validation
- SQLAlchemy ORM for database queries
- Logging: Use Python `logging` module (DEBUG level in dev)
- Error handling: Try/except with HTTPException for API errors
- File structure: Group by feature (services/, agents/, api/)

### Frontend (React/JavaScript)

- Functional components with hooks (useState, useEffect)
- Axios for API calls (centralized in `services/api.js`)
- Lucide icons for UI icons
- Tailwind CSS for styling (utility classes)
- Component structure: One component per file
- Error handling: Try/catch with user-friendly error messages
- Loading states: Show spinners during API calls

### Database

- Never truncate email bodies (CRITICAL)
- Use transactions for multi-table operations
- Index foreign keys for performance
- Normalize data (no duplicate storage)

### Security

- Never commit `secrets.json` to git
- Use environment variables for sensitive data
- Encrypt credentials at rest
- Sanitize user inputs (SQL injection, XSS)

---

## NEXT STEPS

Start with **Phase 1, Task 1.1** (Database Schema). Once complete, move to Task 1.2 (Gmail Service). Follow the critical path for fastest MVP delivery.

**Estimated Timeline**:

- Phase 1: 2-3 days
- Phase 2: 3-4 days
- Phase 3: 1-2 days
- Phase 4: 5-7 days
- Phase 5: 1-2 days
- Phase 6: 2-3 days
- Phase 7: 1 day

**Total**: ~15-22 days for full implementation

---

## IMPORTANT REMINDERS

1. **Port Configuration**: All references to old ports (6900, 5173, 5000) have been updated to new ports (4201, 4202, 4203, 4204)
2. **Never Truncate Emails**: This is a CRITICAL requirement in ARCHITECTURE.md
3. **Altimeter Integration**: Always attempt to link work emails to projects
4. **Local-First**: All data stays local, only API calls to Gemini/Google APIs
5. **Construction Context**: Understand RFIs, submittals, cost codes, daily logs

---

**Good luck! Start building and reference this prompt for task details and validation criteria.**
