# ATLAS QUICK START GUIDE

## For IDE LLMs: Read This First

### What You Need to Know in 60 Seconds

**System**: Atlas (AI assistant) + Altimeter (construction PM) + Davis Projects (knowledge base)

**Ports**:

- Atlas Backend: **4201**
- Atlas Frontend: **4202**
- Altimeter Backend: **4203**
- Altimeter Frontend: **4204**

**Critical Rule**: NEVER truncate email bodies (see ARCHITECTURE.md:274-308)

**Tech Stack**: FastAPI + React + SQLite + ChromaDB + Gemini 2.0 Flash

---

## Three Essential Documents

### 1. **IDE_SYSTEM_CONTEXT.md** ← Read This for Understanding

- Full system architecture explanation
- File locations and data flow
- Integration patterns
- Common tasks and troubleshooting

### 2. **IDE_LLM_BUILD_PROMPT.md** ← Read This for Implementation

- Complete task list with checkboxes
- 7 phases of implementation
- Validation criteria for each task
- Critical path priorities

### 3. **ARCHITECTURE.md** ← Read This for Design Decisions

- Original architecture specification
- Database schema (lines 120-272)
- Email retention rules (lines 274-308)
- Deployment instructions

---

## Start Here: Critical Path

If you're building out Atlas, follow this order:

1. **Database Schema** → `backend/database/models.py`
2. **Gmail Service** → `backend/services/gmail_service.py`
3. **Altimeter Integration** → `backend/services/altimeter_service.py`
4. **Draft Agent** → `backend/agents/draft_agent.py`
5. **Email UI** → `frontend/src/components/email/EmailList.jsx`
6. **API Routes** → `backend/api/email_routes.py`

See `IDE_LLM_BUILD_PROMPT.md` Phase 1 for detailed instructions.

---

## Start Services

### Terminal 1: Backend

```bash
cd C:\Users\mhkem\.atlas\backend
.venv\Scripts\activate
python main.py
```

Access: <http://localhost:4201> (API Docs: <http://localhost:4201/docs>)

### Terminal 2: Frontend

```bash
cd C:\Users\mhkem\.atlas\frontend
npm run dev
```

Access: <http://localhost:4202>

---

## Key Integration Points

### Email → Project Linking

When an email arrives, Atlas:

1. Parses subject/body for project numbers (format: `YY-NNNN`)
2. Queries Altimeter contacts table to match sender
3. Links email to project (`email.project_id`)
4. Categorizes as 'work' if linked

### AI Draft with Context

When generating a draft, Atlas:

1. Checks if email has `project_id`
2. Fetches project context from Altimeter (status, recent activity)
3. Injects context into Gemini prompt
4. Returns draft with project awareness

### Task Extraction

After email sync, Atlas:

1. Analyzes email body with Gemini
2. Extracts action items (description, priority, due date)
3. Creates tasks linked to `email.email_id` and `project_id`
4. Displays in task UI

---

## Files Updated for New Ports

✅ `backend/main.py` - Port 4201
✅ `frontend/vite.config.js` - Port 4202
✅ `backend/core/config.py` - CORS origins
✅ `frontend/src/services/api.js` - API URL
✅ `ARCHITECTURE.md` - All documentation

---

## Common Questions

**Q: Where is the Altimeter database?**
A: `C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db`

**Q: Where are Davis Projects docs?**
A: `C:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive\`

**Q: How do I test email sync?**
A:

1. Set Gmail credentials in `config/secrets.json`
2. Call `gmail_service.sync_emails()`
3. Verify emails in `atlas.db` emails table
4. Check project linking worked

**Q: How do I add a new API endpoint?**
A:

1. Create route function in `api/*_routes.py`
2. Add Pydantic models for request/response
3. Include router in `api/routes.py`
4. Add frontend function in `services/api.js`
5. Test at `/docs`

**Q: What if Gemini API fails?**
A: System should fallback to Ollama local model (needs implementation)

**Q: How do I run tests?**
A: `pytest backend/tests/ -v` (backend) or `npm test` (frontend)

---

## Construction Domain Context

- **RFI**: Request for Information (clarifications to architect)
- **Submittal**: Product data for approval before purchase
- **Cost Code 621**: Electrical homeruns
- **Project Format**: `YY-NNNN` (e.g., `25-0308` = Safe to Sleep project)
- **Strata Level**: Permission level (1-5, where 4+ = admin)

---

## What's Implemented vs Not

### ✅ Implemented

- Basic FastAPI structure
- React frontend with navigation
- Draft agent (Gemini integration)
- Gmail send
- Knowledge base reading
- Document control
- Altimeter connector (basic)

### ❌ Not Implemented (High Priority)

- Email sync and inbox UI
- Task extraction and management UI
- Calendar integration
- Vector search (ChromaDB)
- Background scheduler
- Most API endpoints

See `IDE_LLM_BUILD_PROMPT.md` for full task list.

---

## Emergency Troubleshooting

**Backend won't start?**

- Check `.venv` activated
- Verify port 4201 available: `netstat -ano | findstr 4201`
- Check `config/secrets.json` exists

**Frontend API calls fail?**

- Backend running on 4201?
- Check CORS in `config.py`
- Inspect browser console

**Altimeter connection fail?**

- Verify database path
- Test with: `sqlite3 C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db .tables`

---

## Next Steps

1. Read `IDE_SYSTEM_CONTEXT.md` for full understanding
2. Open `IDE_LLM_BUILD_PROMPT.md` for task list
3. Start with Phase 1, Task 1.1 (Database Schema)
4. Follow critical path priorities
5. Validate each phase before moving on

---

**Good luck building! Reference these docs whenever you need context or task details.**
