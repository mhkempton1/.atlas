# Atlas — Active Task Board

> **Owner**: Michael Kempton | **Last Updated**: 2026-02-12
> This file is the primary work queue for Jules (jules.google.com) and manual development sessions.
> All completed items are archived at the bottom. Focus on **unchecked** items.

---

## 🚀 Next Steps

1. **Test Coverage**: (Done) Implemented `backend/tests/api/test_notification_routes.py` and `backend/tests/services/test_scheduler_service.py`.
2. **AI Hardening**: Add JSON output mode and structured output parsing to `backend/services/ai_service.py`.
3. **Autonomous Loop**: Enhance `backend/scripts/execute_mission.py` to support actual tool execution (file editing, shell commands).

---

## 🔴 Priority 1: Backend Hardening & Testing

### 1.1 Pytest Infrastructure

- [x] Install `pytest`, `pytest-asyncio`, `httpx` (for `TestClient`) as dev dependencies in `backend/requirements.txt`.
- [x] Create `backend/tests/conftest.py` with:
  - A `test_db` fixture using an in-memory SQLite database.
  - A `client` fixture that overrides `get_db` with the test DB and returns a FastAPI `TestClient`.
  - A `mock_ai_service` fixture that patches `services.ai_service.generate_content` to return deterministic JSON.

### 1.2 API Route Tests

- [x] `backend/tests/api/test_task_routes.py` — Test CRUD for `/tasks`: create, read (with filters for status/priority/category), update, delete.
- [x] `backend/tests/api/test_email_routes.py` — Test `/emails/list`, `/emails/{id}`, `/emails/sync`, `/emails/{id}/category`.
- [x] `backend/tests/api/test_calendar_routes.py` — Test `/calendar/events` GET (date range filtering) and POST (event creation with validation).
- [x] `backend/tests/api/test_notification_routes.py` — Test `/notifications/list`, `/notifications/{id}/read`, `/notifications/clear`. Verify unread count decrements correctly.
- [x] `backend/tests/api/test_system_routes.py` — Test `/system/health`, `/system/status`, `/system/dashboard-stats`.

### 1.3 Service-Level Tests

- [x] `backend/tests/services/test_notification_service.py` — Unit test `push_notification`, `get_unread_notifications`, `mark_as_read`, `clear_all`. Verify DB state after each operation.
- [x] `backend/tests/services/test_scheduler_service.py` — Test `get_my_schedule` aggregation logic. Test `get_dashboard_stats` returns correct counts. Mock all DB queries.
- [x] `backend/tests/services/test_ai_service.py` — Test `generate_content` with mocked Gemini API. Verify retry logic on 429 rate limit errors.
- [x] `backend/tests/agents/test_task_agent.py` — Test `extract_tasks_from_email` with sample email bodies. Verify JSON parsing and metadata attachment.

### 1.4 Database Integrity

- [ ] Create `backend/scripts/validate_schema.py` — Script that compares `models.py` definitions against the live `atlas.db` schema and reports missing columns, type mismatches, or missing indexes.
- [ ] Add a DB migration for the `Notification` model if not already applied to the production database. Create `backend/migrate_add_notifications.py`.

---

## 🟠 Priority 2: Intelligence & AI Enhancements

### 2.1 Task Extraction Quality

- [ ] In `backend/agents/task_agent.py`, refine the system prompt to:
  - Require a `confidence` field (0.0–1.0) on each extracted task.
  - Add an `evidence` field that quotes the specific sentence from the source that generated the task.
  - Include rules for deduplication (e.g., "Do not create a task if one with a similar title already exists").
- [ ] In `backend/api/task_routes.py`, update `extract_tasks` and `extract_calendar_tasks` to:
  - Filter out tasks with `confidence < 0.5` by default.
  - Accept an optional `?min_confidence=` query parameter.
  - Return the confidence and evidence in the API response.

### 2.2 AI Service Reliability

- [x] In `backend/services/ai_service.py`:
  - Add structured JSON output mode using Gemini's `response_mime_type: "application/json"` parameter.
  - Implement exponential backoff (not just a flat 60s sleep) for rate limit retries.
  - Add a `max_retries` parameter (default 3) to `generate_content`.
- [ ] Log all AI prompts and responses to `backend/data/ai_audit_log.jsonl` for debugging and prompt refinement.

### 2.3 Learning & Context

- [ ] In `backend/services/learning_service.py`:
  - Implement `get_recent_lessons(limit=10)` to retrieve the most recent learned patterns.
  - Add a `record_lesson(topic, insight, source)` method that persists new learnings to the database.
  - Wire into `ai_service.py` so the system prompt includes recent lessons as context.

---

## 🟡 Priority 3: Frontend Polish & UX

### 3.1 Component Robustness

- [ ] Audit all components in `frontend/src/components/` for missing React imports. Specifically check:
  - `EmailModule.jsx` — ✅ Fixed (was missing `useState`, `useCallback`).
  - `CalendarModule.jsx` — Verify all hooks are imported.
  - `Dashboard.jsx` — Verify all hooks are imported.
  - `TaskList.jsx` — Verify all hooks are imported.
- [ ] Add `ErrorBoundary` wrappers around each major module in `App.jsx` `renderContent()` so a crash in one module doesn't take down the entire app.

### 3.2 Notification UX

- [ ] In `NotificationCenter.jsx`, add notification grouping by type (health, calendar, task, system) with collapsible sections.
- [ ] Add a "Mark All as Read" button (separate from "Clear All" which deletes).
- [ ] Add notification sound/browser notification for high-priority alerts (using the Notification API with user permission).

### 3.3 Dashboard Enhancements

- [ ] In `Dashboard.jsx`, add a "Recent Notifications" widget that shows the last 5 unread notifications inline.
- [ ] Add a "Quick Actions" bar to the dashboard with buttons for: Sync Email, Sync Calendar, Run Watchtower Scan.
- [ ] Improve the Mission Stream component to show task extraction confidence scores when available.

### 3.4 Email Module

- [ ] In `EmailView.jsx`, add a "Create Task from Email" button that calls the existing `extract_tasks` endpoint.
- [ ] In `EmailList.jsx`, add visual indicators for emails that have already had tasks extracted (e.g., a small task icon badge).
- [ ] In `QuickCompose.jsx`, add CC/BCC fields and attachment support (UI only, backend already supports it via SMTP).

---

## 🟢 Priority 4: Infrastructure & DevOps

### 4.1 Cleanup

- [ ] Remove all debug/diagnostic scripts from `backend/` root: `check_db.py`, `debug_imports.py`, `debug_paths.py`, `diagnose_imports.py`, `diagnose_lifespan.py`, `inspect_db.py`, `inspect_db_schema.py`, `inspect_full_db.py`, `troubleshoot_oracle.py`, `verify_app.py`, `verify_fix.py`, `test_altimeter_conn.py`, `test_connections.py`, `test_db_query.py`, `test_engine_pragma.py`, `test_import.py`, `test_weather_service.py`.
- [ ] Remove all debug log/dump files from `backend/` root: `server_debug.log`, `server_log.txt`, `server_log_2.txt`, `server_log_cold.txt`, `server_log_debug.txt`, `server_log_final.txt`, `server_log_final_2.txt`, `server_log_final_3.txt`, `server_log_repair.txt`, `server_log_restart.txt`, `curl_err.txt`, `debug_output.txt`, `db_schema.txt`, `full_db_schema.txt`, `weather_dump.json`, `weather_sim.json`, `full_weather.json`, `final_check.json`, `final_weather_check.json`, `last_response.json`.
- [ ] Move any useful scripts (like `check_schema_direct.py`) into `backend/scripts/` with proper naming.

### 4.2 Documentation

- [ ] Create `backend/README.md` with:
  - Project overview and architecture diagram (Mermaid).
  - Setup instructions (Python version, pip install, database init).
  - API endpoint reference (or link to auto-generated FastAPI docs at `/docs`).
  - Environment variable reference (all `.env` keys).
- [ ] Create `frontend/README.md` with:
  - Component hierarchy overview.
  - Development setup (Node version, npm install, npm run dev).
  - Design system reference (color palette, typography, spacing tokens from `index.css`).

### 4.3 Error Handling

- [ ] In `backend/api/routes.py`, add a global exception handler that catches unhandled exceptions and returns a structured JSON error response with a correlation ID.
- [ ] In `backend/services/notification_service.py`, add deduplication logic: don't push a notification if an identical one (same type + title) was pushed within the last 5 minutes.
- [ ] In `backend/services/status_service.py`, add rate limiting to the health degradation notification so it doesn't spam on every poll cycle.

---

## ✅ Completed (Archive)

<details>
<summary>Click to expand completed items</summary>

- [x] Protocol Implementation (IMAP/SMTP providers, config)
- [x] Intelligence Bridge 2.0 (email routes refactor, Altimeter bridge)
- [x] Internal Persistence (calendar routes)
- [x] UX Restoration (MissionIntelSnippet, EmailList async, TaskList visualization)
- [x] Continuous Improvement Automation (JULES_RUNBOOKS.md, Day/Night cycle)
- [x] IMAP Interactivity (reply, archive, trash, mark unread)
- [x] Frontend Verification (EmailView actions, EmailList API refactor)
- [x] Architecture Refactoring (decoupling, code quality, glassmorphism)
- [x] UI Condensation (TelemetryBar, status indicators)
- [x] Calendar Expansion (CheckSquare fix, POST events, EventCompose)
- [x] Email Suite & Folders (labels, Gmail sync, QuickCompose)
- [x] Notification System (DB model, service, NotificationCenter, user badge)
- [x] Task Extraction from Calendar Events

</details>
