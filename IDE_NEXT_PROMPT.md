# ATLAS SYSTEM - NEXT DEVELOPMENT PROMPT FOR IDE LLM
## Phase 7 - AI Service Resilience & Error Handling (2026-01-28)

## CONTEXT

You are working on **Atlas**, a personal AI assistant platform for construction project management (Davis Electric).

- **Atlas Root**: `C:\Users\mhkem\.atlas\`
- **Backend**: `C:\Users\mhkem\.atlas\backend\` (FastAPI, port 4201)
- **Frontend**: `C:\Users\mhkem\.atlas\frontend\` (React + Vite, port 4202)

### What Was Completed (Phases 1-6)
1. ✅ 70 backend tests passing (0 errors, 0 failures)
2. ✅ All agents functional (Draft, Task, Calendar)
3. ✅ ChromaDB vector search operational
4. ✅ Email sync from Gmail working (200+ emails in DB)
5. ✅ Frontend UX redesigned with shared UIComponents
6. ✅ Real email actions: reply, forward, delete, archive, mark unread, move to folder
7. ✅ CalendarModule shows real events from `/calendar/events` with sync
8. ✅ TaskList with full CRUD: create, update status/priority, delete, filter
9. ✅ EmailView has AI features: Extract Tasks button, AI Draft button, Category selector
10. ✅ Email category filtering in EmailList

### What Needs Work (This Phase)

**PROBLEM**: When calling the AI-powered task extraction endpoint `POST /tasks/extract/{email_id}`, it often fails with:
```json
{"detail":"AI Rate limit exceeded. Please try again later."}
```

The AI service already has retry logic (3 retries with exponential backoff), but:
1. **draft_agent.py** doesn't handle rate limit errors like task_agent does
2. **Error responses are generic** - users don't know when to retry or what to do
3. **No client-side cooldown** - users can spam the button repeatedly
4. **No graceful degradation** - when AI fails, users have no alternative workflow

---

## PRIORITY TASKS (In Order)

### Task 1: Fix Draft Agent Rate Limit Handling
**File**: `C:\Users\mhkem\.atlas\backend\agents\draft_agent.py`

The task_agent properly checks for `ERROR_RATE_LIMIT_EXCEEDED` from ai_service, but draft_agent doesn't. Add the same handling:

```python
# At line 86, REPLACE:
generated_content = await ai_service.generate_content(prompt)

return {
    "draft_text": generated_content,
    "context_used": altimeter_context,
    "status": "generated",
    "model": "gemini-2.0-flash"
}

# WITH:
generated_content = await ai_service.generate_content(prompt)

if generated_content == "ERROR_RATE_LIMIT_EXCEEDED":
    return {
        "draft_text": "",
        "status": "error",
        "error": "AI service is temporarily busy. Please try again in a few seconds.",
        "model": "gemini-2.0-flash",
        "retry_after": 30
    }

if generated_content and generated_content.startswith("Error generating content:"):
    return {
        "draft_text": "",
        "status": "error",
        "error": generated_content,
        "model": "gemini-2.0-flash"
    }

return {
    "draft_text": generated_content or "",
    "context_used": altimeter_context,
    "status": "generated",
    "model": "gemini-2.0-flash"
}
```

---

### Task 2: Improve Task Extraction Error Response
**File**: `C:\Users\mhkem\.atlas\backend\api\task_routes.py`

Update the extract endpoint (lines 152-191) to return more helpful error responses:

```python
@router.post("/extract/{email_id}")
async def extract_tasks(email_id: int, db: Session = Depends(get_db)):
    """Manually trigger AI task extraction for a specific email"""
    from database.models import Email
    from agents.task_agent import task_agent
    from services.altimeter_service import altimeter_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    context = altimeter_service.get_context_for_email(email.from_address, email.subject)
    agent_context = {
        "subject": email.subject,
        "sender": email.from_address,
        "body": email.body_text or "",
        "message_id": email.message_id
    }

    result = await task_agent.process(agent_context)

    # Handle AI service errors with helpful responses
    if result.get("status") != "success":
        error_msg = result.get("error", "Unknown error")

        # Rate limit errors - tell user to retry
        if "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "AI service is temporarily busy",
                    "message": "The AI service is processing many requests. Please try again in 30 seconds.",
                    "retry_after": 30,
                    "fallback": "You can manually create a task from Mission Tasks instead."
                }
            )

        # Other AI errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Task extraction failed",
                "message": error_msg,
                "fallback": "You can manually create a task from Mission Tasks."
            }
        )

    tasks_created = []
    for t_data in result["data"].get("tasks", []):
        task = Task(
            title=t_data["title"],
            description=t_data["description"],
            priority=t_data["priority"].lower(),
            due_date=datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
            project_id=context.get("project", {}).get("number") if context.get("project") else None,
            email_id=email_id,
            created_from="email"
        )
        db.add(task)
        db.flush()
        tasks_created.append({"task_id": task.task_id, "title": task.title})

    db.commit()

    return {
        "tasks_found": len(tasks_created),
        "tasks": tasks_created,
        "email_subject": email.subject
    }
```

---

### Task 3: Improve Draft Endpoint Error Response
**File**: `C:\Users\mhkem\.atlas\backend\api\routes.py`

Update the draft endpoint (lines 26-45) to handle agent errors better:

```python
@router.post("/agents/draft", response_model=DraftResponse)
async def generate_draft_endpoint(request: DraftRequest):
    try:
        context = {
            "subject": request.subject,
            "sender": request.sender,
            "body": request.body,
            "instructions": request.instructions
        }

        result = await draft_agent.process(context)

        # Check for agent errors
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error")
            retry_after = result.get("retry_after")

            if retry_after:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "AI service temporarily unavailable",
                        "message": error_msg,
                        "retry_after": retry_after
                    }
                )
            raise HTTPException(status_code=500, detail=error_msg)

        return DraftResponse(
            draft_text=result.get("draft_text", ""),
            status=result.get("status", "error"),
            model=result.get("model", "unknown"),
            detected_context=result.get("context_used", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Task 4: Add Client-Side Cooldown for AI Buttons
**File**: `C:\Users\mhkem\.atlas\frontend\src\components\email\EmailView.jsx`

Add cooldown state to prevent spamming AI buttons when rate limited:

```jsx
// Add these state variables near the top of the component
const [aiCooldown, setAiCooldown] = useState(false);
const [cooldownSeconds, setCooldownSeconds] = useState(0);

// Add a cooldown effect
useEffect(() => {
    if (cooldownSeconds > 0) {
        const timer = setTimeout(() => setCooldownSeconds(cooldownSeconds - 1), 1000);
        return () => clearTimeout(timer);
    } else {
        setAiCooldown(false);
    }
}, [cooldownSeconds]);

// Helper to start cooldown
const startCooldown = (seconds = 30) => {
    setAiCooldown(true);
    setCooldownSeconds(seconds);
};
```

---

### Task 5: Update handleExtractTasks with Better Error UX
**File**: `C:\Users\mhkem\.atlas\frontend\src\components\email\EmailView.jsx`

Update the handleExtractTasks function to handle 503 errors and show helpful messages:

```jsx
const handleExtractTasks = async () => {
    if (aiCooldown) {
        toast(`Please wait ${cooldownSeconds}s before trying again`, "info");
        return;
    }

    setExtracting(true);
    try {
        const result = await SYSTEM_API.extractTasksFromEmail(email.email_id);
        if (result.tasks_found > 0) {
            toast(`Extracted ${result.tasks_found} task${result.tasks_found > 1 ? 's' : ''} from this email`, "success");
        } else {
            toast("No actionable tasks found in this email", "info");
        }
    } catch (err) {
        const detail = err.response?.data?.detail;

        // Handle structured error response
        if (typeof detail === 'object') {
            toast(detail.message || detail.error, "error");

            // Start cooldown if retry_after is provided
            if (detail.retry_after) {
                startCooldown(detail.retry_after);
            }

            // Show fallback suggestion if provided
            if (detail.fallback) {
                setTimeout(() => {
                    toast(detail.fallback, "info");
                }, 2000);
            }
        } else {
            toast(`Task extraction failed: ${err.message}`, "error");
        }
    } finally {
        setExtracting(false);
    }
};
```

---

### Task 6: Update handleAIDraft with Better Error UX
**File**: `C:\Users\mhkem\.atlas\frontend\src\components\email\EmailView.jsx`

Update the handleAIDraft function similarly:

```jsx
const handleAIDraft = async () => {
    if (aiCooldown) {
        toast(`Please wait ${cooldownSeconds}s before trying again`, "info");
        return;
    }

    setReplyMode('reply');
    setDrafting(true);
    try {
        const result = await SYSTEM_API.generateDraft(
            email.from_address,
            email.subject,
            email.body_text || '',
            'Reply professionally and helpfully'
        );
        if (result.draft_text) {
            setReplyBody(result.draft_text);
            toast("AI draft generated - review and send", "success");
        }
    } catch (err) {
        const detail = err.response?.data?.detail;

        if (typeof detail === 'object') {
            toast(detail.message || detail.error, "error");

            if (detail.retry_after) {
                startCooldown(detail.retry_after);
            }
        } else {
            toast(`Draft generation failed: ${err.message}`, "error");
        }

        // Keep reply mode open so user can type manually
        toast("You can type your reply manually below", "info");
    } finally {
        setDrafting(false);
    }
};
```

---

### Task 7: Add Visual Cooldown Indicator
**File**: `C:\Users\mhkem\.atlas\frontend\src\components\email\EmailView.jsx`

Update the AI buttons to show cooldown state:

```jsx
{/* Extract Tasks Button */}
<button
    className={`btn btn-icon ${aiCooldown
        ? 'bg-gray-500/10 text-gray-500 cursor-not-allowed'
        : 'bg-purple-500/10 hover:bg-purple-500/20 text-purple-400'}`}
    onClick={handleExtractTasks}
    disabled={extracting || aiCooldown}
    title={aiCooldown ? `AI cooldown: ${cooldownSeconds}s` : "AI: Extract Tasks"}
>
    {extracting ? (
        <Loader2 className="w-4 h-4 animate-spin" />
    ) : aiCooldown ? (
        <span className="text-[10px] font-mono">{cooldownSeconds}</span>
    ) : (
        <Brain className="w-4 h-4" />
    )}
</button>

{/* AI Draft Button - in footer */}
<button
    className={`btn btn-secondary flex items-center gap-2 ${aiCooldown
        ? 'bg-gray-500/10 text-gray-500 cursor-not-allowed'
        : 'bg-purple-500/10 hover:bg-purple-500/20 text-purple-400'}`}
    onClick={handleAIDraft}
    disabled={drafting || aiCooldown}
>
    {drafting ? (
        <Loader2 className="w-4 h-4 animate-spin" />
    ) : aiCooldown ? (
        <span className="text-xs font-mono">{cooldownSeconds}s</span>
    ) : (
        <Sparkles className="w-4 h-4" />
    )}
    {aiCooldown ? 'Cooldown' : 'AI Draft'}
</button>
```

---

### Task 8: Add Error Recovery Tests
**File**: `C:\Users\mhkem\.atlas\backend\tests\agents\test_task_agent.py`

Add tests for rate limit error handling:

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_task_agent_rate_limit_handling():
    """Test that task agent properly handles rate limit errors"""
    from agents.task_agent import task_agent

    with patch('agents.task_agent.ai_service') as mock_ai:
        # Simulate rate limit error
        mock_ai.generate_content = AsyncMock(return_value="ERROR_RATE_LIMIT_EXCEEDED")

        result = await task_agent.process({
            "subject": "Test",
            "sender": "test@example.com",
            "body": "Test body"
        })

        assert result["status"] == "error"
        assert "rate limit" in result["error"].lower()

@pytest.mark.asyncio
async def test_task_agent_empty_response_handling():
    """Test that task agent handles empty AI responses"""
    from agents.task_agent import task_agent

    with patch('agents.task_agent.ai_service') as mock_ai:
        mock_ai.generate_content = AsyncMock(return_value=None)

        result = await task_agent.process({
            "subject": "Test",
            "sender": "test@example.com",
            "body": "Test body"
        })

        assert result["status"] == "error"
        assert "empty" in result["error"].lower()
```

---

### Task 9: Add Draft Agent Error Tests
**File**: `C:\Users\mhkem\.atlas\backend\tests\agents\test_draft_agent.py`

Add tests for draft agent error handling:

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_draft_agent_rate_limit_handling():
    """Test that draft agent properly handles rate limit errors"""
    from agents.draft_agent import draft_agent

    with patch('agents.draft_agent.ai_service') as mock_ai:
        mock_ai.generate_content = AsyncMock(return_value="ERROR_RATE_LIMIT_EXCEEDED")

        result = await draft_agent.process({
            "subject": "Test",
            "sender": "test@example.com",
            "body": "Test body",
            "instructions": "Reply professionally"
        })

        assert result["status"] == "error"
        assert result["retry_after"] == 30
        assert result["draft_text"] == ""

@pytest.mark.asyncio
async def test_draft_agent_error_response_handling():
    """Test that draft agent handles AI error responses"""
    from agents.draft_agent import draft_agent

    with patch('agents.draft_agent.ai_service') as mock_ai:
        mock_ai.generate_content = AsyncMock(return_value="Error generating content: API key invalid")

        result = await draft_agent.process({
            "subject": "Test",
            "sender": "test@example.com",
            "body": "Test body",
            "instructions": "Reply professionally"
        })

        assert result["status"] == "error"
        assert "error" in result["error"].lower()
```

---

## CODING STANDARDS

- Keep existing functionality — only improve error handling
- Use 503 status for rate limits (indicates temporary unavailability)
- Use 500 status for other errors
- Error responses should include `message`, `retry_after` (if applicable), and `fallback`
- Client cooldown prevents spamming during rate limits
- All tests should still pass

---

## VALIDATION

### 1. Backend Tests
```bash
cd C:\Users\mhkem\.atlas
python -m pytest backend/tests/ -v --tb=short
```
Target: 70 existing tests + 4 new error handling tests = 74 tests passing

### 2. Rate Limit Simulation Test
```bash
# Run multiple rapid requests to trigger rate limit
for i in {1..10}; do curl -X POST http://localhost:4201/api/v1/tasks/extract/1; done
```
Expected: After a few requests, should return 503 with helpful message instead of generic 500.

### 3. Frontend Verification
```bash
cd C:\Users\mhkem\.atlas\frontend
npm run dev
```
- Click "Extract Tasks" rapidly → see cooldown start after rate limit
- Click "AI Draft" → if rate limited, see cooldown indicator
- Cooldown countdown visible on both buttons
- Helpful error messages in toasts

---

## IMPORTANT NOTES

1. **Don't change ai_service.py**: It already has proper retry logic (3 retries with exponential backoff). The issue is how agents and routes handle the final failure.

2. **503 vs 500**: Use 503 Service Unavailable for rate limits (temporary), 500 for other errors (something broke).

3. **Structured error responses**: Return objects with `error`, `message`, `retry_after`, `fallback` so frontend can handle gracefully.

4. **Don't remove existing features**: This phase only adds error handling improvements to existing code.

5. **useEffect cleanup**: The cooldown timer needs proper cleanup to avoid memory leaks.

---

## AFTER COMPLETION

Report back with:
1. Test results (pass/fail counts)
2. Rate limit handling working (503 responses)
3. Frontend cooldown working
4. Error messages improved
5. Any issues encountered

**Generated by Claude Opus 4.5 - 2026-01-28**
