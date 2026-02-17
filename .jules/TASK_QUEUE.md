# Jules Task Queue

**Purpose**: Organized task delegation to Jules with clear priorities and dependencies

---

## 🔴 **CRITICAL PRIORITY (Do First)**

### Task 1: Build Real Altimeter Bidirectional Sync

**Status**: 📋 Ready for Jules
**Estimated Time**: 1 week
**Dependencies**: None
**GitHub Branch**: `altimeter-bidirectional-sync`

**Prompt for Jules**:

```
I need to build a production-grade bidirectional sync between Atlas and Altimeter for construction project management.

CONTEXT:
- Atlas is a FastAPI backend + React frontend
- Altimeter is our construction management platform with REST API
- Current integration is read-only snapshots (stale data)
- We need real-time sync with conflict resolution

GOAL:
Implement bidirectional sync so changes in Atlas push to Altimeter and vice versa, with real-time updates.

TECHNICAL REQUIREMENTS:

1. Create Sync Queue Service (backend/services/altimeter_sync_service.py):
   - Queue-based sync engine (use Python's asyncio queue)
   - Track sync status per entity (pending, syncing, synced, error)
   - Implement exponential backoff for retries
   - Store sync metadata in database (last_synced_at, sync_status, error_log)

2. Add Database Tables for Sync Tracking:
   - Create migration: backend/migrate_add_sync_queue.py
   - SyncQueue table: (entity_type, entity_id, direction, status, retry_count, last_attempt, error_message)
   - SyncHistory table: (audit log of all sync operations)

3. Implement Webhook Receiver (backend/api/altimeter_webhooks.py):
   - POST /webhooks/altimeter - receive updates from Altimeter
   - Verify webhook signature for security
   - Parse webhook payload and queue updates
   - Return 200 OK immediately (async processing)

4. Build Bidirectional Sync Logic:

   A) Atlas → Altimeter (Push):
   - When task created in Atlas, push to Altimeter API
   - When task updated in Atlas, update in Altimeter
   - Handle conflicts: if Altimeter version newer, queue conflict for user

   B) Altimeter → Atlas (Pull via Webhooks):
   - Receive webhook when task changes in Altimeter
   - Update Atlas database with new data
   - Handle conflicts: use "last write wins" with timestamp comparison

   C) Conflict Resolution:
   - If both systems updated same entity within 5 min → create conflict record
   - Show conflict in UI for manual resolution
   - Store both versions until resolved

5. Add Real-time Updates to Frontend:
   - Implement WebSocket endpoint: /ws/sync-status
   - Emit events when sync completes: {entity_type, entity_id, status}
   - Update UI components to listen for sync events
   - Show sync status badges on tasks ("Syncing...", "Synced ✓", "Conflict ⚠️")

6. Error Handling & Monitoring:
   - Log all sync operations to structured JSON
   - Create /api/v1/sync/status endpoint for monitoring
   - Add retry logic: 3 attempts with exponential backoff (5s, 25s, 125s)
   - Alert on repeated failures (>5 consecutive errors)

7. Testing:
   - Unit tests for sync queue logic
   - Integration test: Create task in Atlas → verify appears in Altimeter
   - Integration test: Webhook from Altimeter → verify updates Atlas
   - Conflict test: Update same task in both systems → verify conflict created

DELIVERABLES:
- ✅ altimeter_sync_service.py (sync engine)
- ✅ migrate_add_sync_queue.py (database migration)
- ✅ altimeter_webhooks.py (webhook receiver)
- ✅ WebSocket endpoint for real-time updates
- ✅ Updated Task model with sync fields
- ✅ Frontend components showing sync status
- ✅ Integration tests proving bidirectional sync works

ACCEPTANCE CRITERIA:
1. Can create task in Atlas → appears in Altimeter within 10 seconds
2. Can update task in Altimeter → updates in Atlas within 10 seconds
3. Conflicts are detected and flagged for manual resolution
4. Sync status visible in UI (syncing, synced, error badges)
5. Failed syncs retry automatically with exponential backoff
6. All sync operations logged for debugging

FILES TO CREATE/MODIFY:
- backend/services/altimeter_sync_service.py (NEW)
- backend/api/altimeter_webhooks.py (NEW)
- backend/migrate_add_sync_queue.py (NEW)
- backend/database/models.py (MODIFY - add sync fields)
- backend/api/task_routes.py (MODIFY - trigger sync on create/update)
- frontend/src/services/websocket.js (NEW - WebSocket client)
- frontend/src/components/tasks/TaskList.jsx (MODIFY - show sync status)

IMPORTANT NOTES:
- Use existing altimeter_service.py for API calls (already has auth)
- Follow existing FastAPI patterns in codebase
- Use SQLAlchemy models from database/models.py
- Match existing code style (JetBrains Mono font comments, etc.)
- Test with REAL Altimeter API (staging environment available)

Please implement this in phases:
Phase 1 (Day 1-2): Database schema + sync queue service
Phase 2 (Day 3-4): Webhook receiver + Atlas→Altimeter push
Phase 3 (Day 5-6): Conflict resolution + real-time updates
Phase 4 (Day 7): Testing + documentation

After each phase, commit to branch `altimeter-bidirectional-sync` and I'll review before you continue.
```

**Validation Checklist** (Claude will verify after Jules pushes):

- [ ] Sync queue service created with proper error handling
- [ ] Database migration runs without errors
- [ ] Webhook endpoint returns 200 OK and queues updates
- [ ] Tasks sync from Atlas → Altimeter
- [ ] Tasks sync from Altimeter → Atlas
- [ ] Conflicts detected and flagged
- [ ] WebSocket updates work in frontend
- [ ] Integration tests pass

---

## 🟡 **HIGH PRIORITY (After Task 1)**

### Task 2: Standardize Service Layer Architecture

**Status**: 📋 Ready for Jules
**Estimated Time**: 5 days
**Dependencies**: None (can run parallel to Task 1)
**GitHub Branch**: `service-layer-refactor`

**Prompt for Jules**:

```
The Atlas backend has inconsistent service patterns. Some routes use direct DB queries, others try to import non-existent service classes. We need a consistent service layer.

GOAL:
Create standardized service classes for all business logic, following single pattern throughout codebase.

PATTERN TO FOLLOW:
```python
# services/task_service.py
class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_data: dict) -> Task:
        # Business logic here
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    # ... etc

# Singleton instance
task_service = TaskService
```

SERVICES TO CREATE:

1. TaskService (backend/services/task_service.py)
2. EmailService (backend/services/email_service.py)
3. CalendarService (backend/services/calendar_service.py)
4. ProjectService (backend/services/project_service.py)

ROUTES TO REFACTOR:

- backend/api/task_routes.py → use TaskService
- backend/api/email_routes.py → use EmailService
- backend/api/calendar_routes.py → use CalendarService
- backend/api/dashboard_routes.py → use all services

REQUIREMENTS:

- Each service class takes db: Session in constructor
- All business logic moves from routes to services
- Routes become thin controllers (validate input → call service → return response)
- Maintain existing API contracts (don't break frontend)
- Add type hints for all methods
- Write docstrings for public methods

DELIVERABLES:

- ✅ 4 new service classes
- ✅ All routes refactored to use services
- ✅ No direct db.query() calls in route handlers
- ✅ Existing tests still pass

Please commit incrementally:

- Commit 1: Create TaskService + refactor task_routes.py
- Commit 2: Create EmailService + refactor email_routes.py
- Commit 3: Create CalendarService + refactor calendar_routes.py
- Commit 4: Create ProjectService + refactor dashboard_routes.py

```

**Validation Checklist**:
- [ ] All service classes follow same pattern
- [ ] Routes are thin (< 20 lines per endpoint)
- [ ] No direct DB queries in routes
- [ ] Type hints on all methods
- [ ] Existing API tests pass

---

### Task 3: Email Intelligence - Construction Document Classifier
**Status**: 📋 Ready for Jules
**Estimated Time**: 1 week
**Dependencies**: Task 2 (EmailService)
**GitHub Branch**: `email-document-classifier`

**Prompt for Jules**:
```

I need to implement a specialized Construction Document Classifier for our Email Intelligence system.

GOAL:
Categorize incoming emails into specific construction document types (RFI, Submittal, Change Order, Drawing, Specification) and store extracted metadata.

TECHNICAL REQUIREMENTS:

1. Create a Document Classifier Service (backend/services/document_classifier_service.py):
   - Use LLM-based classification via ai_service.py.
   - Detect: Doc Type, Document Number (if any), Project Number, Urgency, and Key Actions.
   - Return structured JSON output.

2. Database Schema (backend/migrate_add_ext_docs.py):
   - Create Table: `extracted_documents` (id, email_id, doc_type, doc_number, project_id, status, metadata_json, created_at).

3. Integrate with TaskAgent (backend/agents/task_agent.py):
   - When processing an email, first run it through DocumentClassifierService.
   - Use the classifier's output to seed the task extraction prompt.

4. Update Email Persistence (backend/services/email_persistence_service.py):
   - Automatically trigger classification for new emails arriving from the IMAP/Gmail sync.

DELIVERABLES:

- ✅ document_classifier_service.py
- ✅ migrate_add_ext_docs.py
- ✅ Updated TaskAgent
- ✅ Integration tests for document classification

```

---

## 🟢 **MEDIUM PRIORITY (After High Priority)**

### Task 4: Project Health Dashboard with Risk Scoring
**Status**: 🔜 Pending
**Estimated Time**: 2 weeks
**Dependencies**: Task 1 (Altimeter sync)

### Task 5: Mobile-First Field Views (PWA)
**Status**: 🔜 Pending
**Estimated Time**: 1 week
**Dependencies**: Task 1 (Altimeter sync)

---

## 📊 **Progress Tracking**

| Task | Status | Start Date | Completion Date | Notes |
|------|--------|------------|-----------------|-------|
| Task 1: Altimeter Sync | 📋 Ready | - | - | Waiting to send to Jules |
| Task 2: Service Layer | 📋 Ready | - | - | Can run parallel |
| Task 3: Email Classifier | 🔜 Pending | - | - | Needs Task 2 |
| Task 4: Health Dashboard | 🔜 Pending | - | - | Needs Task 1 |
| Task 5: Mobile Views | 🔜 Pending | - | - | Needs Task 1 |

---

## 🔄 **Workflow**

### **When You Send Task to Jules**:
1. Copy the "Prompt for Jules" section
2. Send to jules.google.com
3. Update task status to "🔄 In Progress"
4. Note the start date

### **When Jules Pushes to GitHub**:
1. Tag me: "Jules pushed Task X to branch Y, please validate"
2. I'll pull latest, run tests, verify requirements
3. I'll update this doc with validation results
4. If approved → merge to master, mark task ✅ Complete
5. If issues → create feedback for Jules, she fixes and re-pushes

### **Parallelization**:
- Task 1 and Task 2 can run simultaneously (different files)
- Task 3 requires Task 2 complete (depends on EmailService)
- Task 4 and 5 require Task 1 complete (depend on Altimeter sync)

---

## 📝 **Notes for Claude**

**When validating Jules' work, check**:
- [ ] Code follows existing patterns in codebase
- [ ] Type hints present and accurate
- [ ] Error handling implemented
- [ ] Tests written and passing
- [ ] Database migrations run cleanly
- [ ] API contracts maintained (no breaking changes)
- [ ] Documentation updated
- [ ] No import errors
- [ ] No security vulnerabilities (SQL injection, etc.)
- [ ] Performance acceptable (no N+1 queries)

**Common Issues to Watch For**:
- Import paths (Jules might use wrong module structure)
- Database session management (forgot to commit/rollback)
- Async/await mismatches (mixing sync and async)
- Missing error handling
- Hardcoded values instead of config
- Not following existing code style

---

**Last Updated**: 2026-02-15
**Maintained By**: Claude (Code Review Agent)
