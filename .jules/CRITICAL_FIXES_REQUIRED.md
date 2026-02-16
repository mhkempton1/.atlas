# CRITICAL FIXES REQUIRED - Altimeter Sync
**Priority**: 🔴 BLOCKING - Must Complete Before Any Production Use
**Estimated Time**: 11 hours (1.5 days)
**Branch**: `altimeter-sync-critical-fixes`

---

## RUTHLESS STANDARDS

This is **construction software managing $10M+ projects**. We don't ship prototypes. We ship production-grade systems that work under stress, handle failures gracefully, and protect user data.

**Your previous delivery was 60% complete**. This prompt fixes the critical 40% that's missing.

**Everything below is MANDATORY**. No "TODO" comments. No mock implementations. No skipped tests.

---

## 🔴 CRITICAL FIX #1: Implement WebSocket Manager

### **Problem**
You reference `self._ws_manager` throughout `altimeter_sync_service.py` but **never created the WebSocket manager**. Real-time UI updates don't work.

### **Solution: Create services/websocket_manager.py**

```python
# backend/services/websocket_manager.py
from fastapi import WebSocket
from typing import List, Dict, Any
import logging
import json

logger = logging.getLogger("websocket_manager")

class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts sync status updates to connected clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_sync_status(self, entity_type: str, entity_id: int, status: str):
        """
        Broadcast sync status to all connected clients.

        Args:
            entity_type: Type of entity ('task', 'email', etc.)
            entity_id: Database ID of the entity
            status: Sync status ('syncing', 'synced', 'error', 'conflict')
        """
        message = {
            "type": "sync_status",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.debug(f"Broadcast to client: {message}")
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for dead in dead_connections:
            await self.disconnect(dead)

        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connections")

# Singleton instance
ws_manager = WebSocketManager()
```

### **Wire Into FastAPI (backend/core/app.py)**

Add WebSocket endpoint:

```python
# backend/core/app.py
from fastapi import WebSocket, WebSocketDisconnect
from services.websocket_manager import ws_manager
from services.altimeter_sync_service import altimeter_sync_service

# After app = FastAPI() and before other routes...

# Set WebSocket manager in sync service
altimeter_sync_service.set_ws_manager(ws_manager)

@app.websocket("/ws/sync-status")
async def websocket_sync_status(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sync status updates.
    Frontend connects here to receive sync events.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages (if any)
            data = await websocket.receive_text()
            # We don't expect clients to send data, but this keeps connection open
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)
```

### **Acceptance Criteria**
- [ ] `services/websocket_manager.py` exists and imports without errors
- [ ] WebSocket endpoint `/ws/sync-status` is registered in FastAPI
- [ ] Frontend can connect to `ws://localhost:4201/ws/sync-status`
- [ ] When sync runs, frontend receives JSON message: `{"type": "sync_status", "entity_id": 123, "status": "synced"}`
- [ ] Manual test: Open browser console, connect WebSocket, trigger sync, see message

---

## 🔴 CRITICAL FIX #2: Implement Conflict Detection

### **Problem**
Current code **blindly overwrites local changes** with remote data. No conflict detection = DATA LOSS.

### **Solution: Add Conflict Table (backend/migrate_add_sync_conflicts.py)**

```python
# backend/migrate_add_sync_conflicts.py
from database.database import engine, Base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime, timezone

class SyncConflict(Base):
    __tablename__ = "sync_conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # 'task', 'email', etc.
    entity_id = Column(Integer, nullable=False)
    local_version = Column(JSON, nullable=False)  # Snapshot of local data
    remote_version = Column(JSON, nullable=False)  # Snapshot of remote data
    status = Column(String(20), default='unresolved')  # 'unresolved', 'resolved_local', 'resolved_remote'
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

def run_migration():
    print("Creating sync_conflicts table...")
    SyncConflict.__table__.create(engine, checkfirst=True)
    print("Migration complete.")

if __name__ == "__main__":
    run_migration()
```

### **Add Conflict Model (backend/database/models.py)**

Add to models.py:

```python
class SyncConflict(Base):
    __tablename__ = "sync_conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    local_version = Column(JSON, nullable=False)
    remote_version = Column(JSON, nullable=False)
    status = Column(String(20), default='unresolved')
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### **Implement Conflict Detection Logic (backend/services/altimeter_sync_service.py)**

Replace `_sync_pull_task` with:

```python
async def _sync_pull_task(self, item: SyncQueue, db: Session):
    """Pulls a remote task from Altimeter with conflict detection."""
    task = db.query(Task).filter(Task.task_id == item.entity_id).first()
    if not task:
        return

    remote_id = task.remote_id or task.related_altimeter_task_id
    if not remote_id:
        return

    remote_task = await altimeter_api_service.get_task(remote_id)
    if not remote_task:
        return

    # CONFLICT DETECTION
    local_updated = task.updated_at if task.updated_at else task.created_at
    remote_updated_str = remote_task.get("updated_at")
    last_sync = task.last_synced_at

    if remote_updated_str:
        remote_updated = datetime.fromisoformat(remote_updated_str.replace('Z', '+00:00'))

        # Check if both changed since last sync
        if last_sync and local_updated > last_sync and remote_updated > last_sync:
            # CONFLICT: Both sides changed
            time_delta = abs((local_updated - remote_updated).total_seconds())

            if time_delta < 300:  # Within 5 minutes
                # Create conflict record
                from database.models import SyncConflict

                conflict = SyncConflict(
                    entity_type='task',
                    entity_id=task.task_id,
                    local_version={
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "updated_at": local_updated.isoformat()
                    },
                    remote_version={
                        "title": remote_task.get("title"),
                        "description": remote_task.get("description"),
                        "status": remote_task.get("status"),
                        "priority": remote_task.get("priority"),
                        "due_date": remote_task.get("due_date"),
                        "updated_at": remote_updated.isoformat()
                    },
                    status='unresolved'
                )
                db.add(conflict)

                # Mark sync item as conflict
                item.status = 'conflict'
                task.sync_status = 'conflict'

                logger.warning(f"Conflict detected for task {task.task_id}")

                # Notify UI
                if self._ws_manager:
                    await self._ws_manager.broadcast_sync_status('task', task.task_id, 'conflict')

                return  # Don't auto-merge

    # No conflict, safe to merge
    task.title = remote_task.get("title", task.title)
    task.description = remote_task.get("description", task.description)
    task.status = remote_task.get("status", task.status)
    task.priority = remote_task.get("priority", task.priority)

    if remote_task.get("due_date"):
        task.due_date = datetime.fromisoformat(remote_task["due_date"])

    task.last_synced_at = datetime.now(timezone.utc)
    task.sync_status = 'synced'
```

### **Add Conflict Resolution API (backend/api/sync_routes.py)**

Add endpoint to resolve conflicts:

```python
@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    resolution: Dict[str, str],  # {"choice": "local" or "remote"}
    db: Session = Depends(get_db)
):
    """
    Resolve a sync conflict by choosing local or remote version.
    """
    from database.models import SyncConflict, Task

    conflict = db.query(SyncConflict).filter(SyncConflict.id == conflict_id).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    task = db.query(Task).filter(Task.task_id == conflict.entity_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    choice = resolution.get("choice")

    if choice == "local":
        # Keep local, push to remote
        altimeter_sync_service.enqueue_task(db, task.task_id, "push")
        conflict.status = "resolved_local"
    elif choice == "remote":
        # Accept remote, update local
        remote_data = conflict.remote_version
        task.title = remote_data.get("title", task.title)
        task.description = remote_data.get("description", task.description)
        task.status = remote_data.get("status", task.status)
        task.priority = remote_data.get("priority", task.priority)
        task.sync_status = "synced"
        conflict.status = "resolved_remote"
    else:
        raise HTTPException(status_code=400, detail="Invalid choice")

    conflict.resolved_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "resolved", "choice": choice}
```

### **Acceptance Criteria**
- [ ] `SyncConflict` table created by migration
- [ ] Conflict detection code compares timestamps correctly
- [ ] When both versions changed within 5 min, conflict record created
- [ ] Sync status becomes 'conflict' instead of 'synced'
- [ ] Frontend receives WebSocket message with status='conflict'
- [ ] Conflict resolution API works: POST to `/conflicts/{id}/resolve` with `{"choice": "local"}` or `{"choice": "remote"}`
- [ ] After resolution, task syncs correctly

---

## 🔴 CRITICAL FIX #3: Replace Mock Altimeter API with Real Implementation

### **Problem**
`altimeter_api_service.py` returns fake data. Nothing actually talks to Altimeter.

### **Solution: Implement Real HTTP Client (backend/services/altimeter_api_service.py)**

Replace ENTIRE FILE with:

```python
# backend/services/altimeter_api_service.py
import aiohttp
import logging
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger("altimeter_api")

class AltimeterAPIService:
    """
    Real HTTP client for Altimeter construction management API.
    """
    def __init__(self):
        self.base_url = getattr(settings, "ALTIMETER_API_URL", "https://api.altimeter.com/v1")
        self.api_key = getattr(settings, "ALTIMETER_API_KEY", "")

        if not self.api_key:
            logger.warning("ALTIMETER_API_KEY not configured. API calls will fail.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in Altimeter."""
        url = f"{self.base_url}/tasks"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=task_data, headers=self._headers(), timeout=10) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        logger.info(f"Created Altimeter task: {result.get('id')}")
                        return result
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        raise Exception(f"Altimeter API returned {resp.status}: {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error creating task: {e}")
                raise

    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task in Altimeter."""
        url = f"{self.base_url}/tasks/{task_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(url, json=task_data, headers=self._headers(), timeout=10) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(f"Updated Altimeter task: {task_id}")
                        return result
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        raise Exception(f"Altimeter API returned {resp.status}: {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error updating task: {e}")
                raise

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a task from Altimeter by ID."""
        url = f"{self.base_url}/tasks/{task_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self._headers(), timeout=10) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    elif resp.status == 404:
                        logger.warning(f"Task {task_id} not found in Altimeter")
                        return None
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        raise Exception(f"Altimeter API returned {resp.status}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error fetching task: {e}")
                raise

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task in Altimeter."""
        url = f"{self.base_url}/tasks/{task_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.delete(url, headers=self._headers(), timeout=10) as resp:
                    if resp.status in [200, 204]:
                        logger.info(f"Deleted Altimeter task: {task_id}")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.error(f"Altimeter API error {resp.status}: {error_text}")
                        return False
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error deleting task: {e}")
                return False

# Singleton instance
altimeter_api_service = AltimeterAPIService()
```

### **Add Config Variables (backend/core/config.py)**

Add to Settings class:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    ALTIMETER_API_URL: str = "https://api.altimeter.com/v1"
    ALTIMETER_API_KEY: str = ""  # Set via environment variable
```

### **Acceptance Criteria**
- [ ] `aiohttp` installed (`pip install aiohttp`)
- [ ] Real HTTP requests to Altimeter API
- [ ] Proper error handling for network failures
- [ ] 10-second timeout on all requests
- [ ] Correct Authorization header with Bearer token
- [ ] Logs all API calls (success and failure)
- [ ] Manual test: Set `ALTIMETER_API_KEY` in `.env`, trigger sync, verify HTTP request in Altimeter logs

---

## 🔴 CRITICAL FIX #4: Create End-to-End Integration Test

### **Problem**
No proof this works with real Altimeter. Zero confidence in production.

### **Solution: Create Manual Test Procedure (backend/tests/manual_e2e_test.md)**

```markdown
# Manual End-to-End Sync Test

## Prerequisites
1. Altimeter staging environment accessible
2. `ALTIMETER_API_KEY` set in `.env`
3. `ALTIMETER_API_URL` pointing to staging
4. Backend running on port 4201
5. Frontend running on port 4202

## Test Procedure

### Test 1: Atlas → Altimeter Push (Create)
1. Open Atlas UI: http://localhost:4202
2. Navigate to Tasks
3. Click "Create Task"
4. Fill in:
   - Title: "E2E Test Task - [timestamp]"
   - Description: "Testing sync from Atlas to Altimeter"
   - Priority: High
   - Due Date: Tomorrow
5. Click "Save"
6. **Expected**: Task appears in Atlas with "Syncing..." badge
7. Wait 5 seconds
8. **Expected**: Badge changes to "Synced ✓"
9. Open Altimeter staging UI
10. Search for task by title
11. **PASS IF**: Task exists in Altimeter with same title, description, priority, due date

### Test 2: Altimeter → Atlas Pull (Webhook)
1. Open Altimeter staging UI
2. Create new task:
   - Title: "E2E Test from Altimeter - [timestamp]"
   - Status: Open
   - Priority: Medium
3. Save task
4. **Expected**: Altimeter sends webhook to Atlas
5. Wait 5 seconds
6. Open Atlas UI
7. Refresh task list
8. **PASS IF**: New task appears in Atlas with same data

### Test 3: Conflict Detection
1. In Atlas: Edit task "Test Conflict" → Change title to "Atlas Version"
2. Wait 1 second (don't sync yet)
3. In Altimeter: Edit same task → Change title to "Altimeter Version"
4. Trigger Atlas sync
5. **Expected**: Conflict modal appears in Atlas UI
6. **Expected**: Shows both versions side-by-side
7. Click "Keep Local Version"
8. **Expected**: Conflict resolved, task title in Altimeter updates to "Atlas Version"
9. **PASS IF**: Both systems now show "Atlas Version"

### Test 4: WebSocket Real-Time Updates
1. Open browser console in Atlas UI
2. Run: `const ws = new WebSocket('ws://localhost:4201/ws/sync-status'); ws.onmessage = (e) => console.log(JSON.parse(e.data));`
3. Create new task in Atlas
4. **Expected**: Console shows: `{"type": "sync_status", "entity_id": 123, "status": "syncing"}`
5. Wait 5 seconds
6. **Expected**: Console shows: `{"type": "sync_status", "entity_id": 123, "status": "synced"}`
7. **PASS IF**: Real-time messages received

## Pass Criteria
- All 4 tests must pass
- No errors in backend logs
- No errors in browser console
- Sync completes within 10 seconds
```

### **Acceptance Criteria**
- [ ] Manual test document created
- [ ] You have PERSONALLY run all 4 tests
- [ ] All 4 tests PASS
- [ ] Screenshots of passing tests attached to PR
- [ ] Any failures documented with root cause and fix

---

## DELIVERABLES CHECKLIST

### **Files to Create**:
- [ ] `backend/services/websocket_manager.py` (NEW)
- [ ] `backend/migrate_add_sync_conflicts.py` (NEW)
- [ ] `backend/tests/manual_e2e_test.md` (NEW)

### **Files to Modify**:
- [ ] `backend/core/app.py` (add WebSocket endpoint)
- [ ] `backend/database/models.py` (add SyncConflict model)
- [ ] `backend/services/altimeter_sync_service.py` (add conflict detection to `_sync_pull_task`)
- [ ] `backend/services/altimeter_api_service.py` (replace ALL mock code with real HTTP)
- [ ] `backend/api/sync_routes.py` (add conflict resolution endpoint)
- [ ] `backend/core/config.py` (add Altimeter API settings)

### **Tests to Pass**:
- [ ] All existing tests still pass
- [ ] WebSocket connection test passes
- [ ] Conflict detection unit test passes
- [ ] All 4 manual E2E tests pass

### **Documentation to Provide**:
- [ ] Screenshots of passing E2E tests
- [ ] Commit messages that reference issue numbers
- [ ] No TODO comments in code
- [ ] All functions have docstrings

---

## COMMIT STRATEGY

Commit incrementally with clear messages:

```bash
git commit -m "feat: implement WebSocket manager for real-time sync updates"
git commit -m "feat: add conflict detection with timestamp comparison"
git commit -m "feat: replace mock Altimeter API with real HTTP client"
git commit -m "test: add end-to-end sync validation tests"
git commit -m "fix: add SyncConflict model and resolution endpoint"
```

---

## TESTING BEFORE YOU PUSH

Before pushing ANYTHING:

1. Run: `python -m pytest tests/ -v`
2. Run: `python -c "from services.websocket_manager import ws_manager; print('WebSocket: OK')"`
3. Run: `python -c "from database.models import SyncConflict; print('Conflict model: OK')"`
4. Run: `python backend/migrate_add_sync_conflicts.py`
5. Start backend, check logs for "WebSocket Manager initialized"
6. Open browser, connect to `ws://localhost:4201/ws/sync-status`, verify connection accepted

If ANY of these fail, DO NOT PUSH.

---

## FINAL STANDARDS

- **No mock implementations** (everything must be real)
- **No TODO comments** (finish what you start)
- **No skipped tests** (write tests for new code)
- **No silent failures** (log errors, raise exceptions)
- **No assumptions** (test with real Altimeter API)

**This is production-grade construction software. We hold the highest bar.**

Push to branch `altimeter-sync-critical-fixes` when ALL acceptance criteria met.
