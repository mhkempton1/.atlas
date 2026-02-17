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
