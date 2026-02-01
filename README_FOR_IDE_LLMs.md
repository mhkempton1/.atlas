# README FOR IDE LLMs

## Welcome! You're working on the Atlas project

This document helps you quickly understand which documentation to read based on your task.

---

## 📚 DOCUMENTATION MAP

We have **4 specialized prompts** for different purposes:

### 1. **QUICK_START_GUIDE.md** ← Start Here (5 min read)

**When to use**: First time working on Atlas, need quick orientation
**Contains**:

- 60-second system overview
- Port architecture (4201/4202/4203/4204)
- How to start services
- Common questions FAQ
- Where to find things

**Read this first**, then choose your path below.

---

### 2. **IDE_SYSTEM_CONTEXT.md** ← Understanding the System (20 min read)

**When to use**: Need to understand architecture, integration patterns, tech stack
**Contains**:

- Complete system architecture (Atlas + Altimeter + Davis Projects)
- Data flow and integration patterns
- Database schema reference
- API endpoints (existing and needed)
- File structure and locations
- How Atlas ↔ Altimeter integration works
- Troubleshooting guide
- Quick reference commands

**Use this when**:

- ✅ Adding new features that touch multiple systems
- ✅ Debugging integration issues
- ✅ Need to understand data flow
- ✅ Writing code that connects backend ↔ frontend
- ✅ Need context on construction domain (RFIs, submittals, cost codes)

---

### 3. **IDE_LLM_BUILD_PROMPT.md** ← Building Out Features (30 min read)

**When to use**: Implementing new features, following structured development plan
**Contains**:

- **7-Phase Implementation Plan** with checkboxes:
  - Phase 1: Core Infrastructure (Database, Gmail, Altimeter)
  - Phase 2: AI Agents (Draft, Task, Calendar, Project)
  - Phase 3: Vector Search & RAG (ChromaDB)
  - Phase 4: Frontend Implementation (Email, Tasks, Calendar, Dashboard)
  - Phase 5: Background Jobs & Automation
  - Phase 6: Testing & Validation
  - Phase 7: Documentation & Deployment
- Detailed task lists with validation criteria
- Critical path priorities
- Coding standards (Python/React)
- Timeline estimates

**Use this when**:

- ✅ Building new features from scratch
- ✅ Need structured task breakdown
- ✅ Want to follow MVP critical path
- ✅ Need validation criteria for testing
- ✅ Implementing database schema, API endpoints, UI components

---

### 4. **IDE_AUDIT_PROMPT.md** ← Finding Problems (45 min read)

**When to use**: Auditing code quality, finding bugs, identifying UX issues
**Contains**:

- **6 Audit Categories**:
  1. Error Detection (imports, types, API calls)
  2. Incomplete Implementations (stubs, TODOs, missing features)
  3. UX Friction Analysis (loading states, errors, empty states, navigation)
  4. Performance Bottlenecks (N+1 queries, large payloads, slow renders)
  5. Security Vulnerabilities (XSS, SQL injection, exposed secrets)
  6. Integration Gaps (broken Atlas ↔ Altimeter connections)
- Audit checklists for backend/frontend/integration/security
- Issue reporting templates
- Priority classification (Critical/High/Medium/Low)

**Use this when**:

- ✅ Code review / quality check
- ✅ Debugging errors or broken features
- ✅ Improving user experience
- ✅ Optimizing performance
- ✅ Security hardening
- ✅ Before deployment (production readiness check)

---

### 5. **ARCHITECTURE.md** ← Reference Specification (60 min read)

**When to use**: Need authoritative design decisions, database schema, original vision
**Contains**:

- Official architecture specification v2.0
- Complete database schema (lines 120-272)
- **CRITICAL RULE**: Never truncate email bodies (lines 274-308)
- AI agent designs
- Deployment instructions
- Success metrics

**Use this when**:

- ✅ Need to verify design decisions
- ✅ Implementing database models
- ✅ Designing new features (ensure alignment with vision)
- ✅ Resolving conflicting information (ARCHITECTURE.md is authoritative)

---

## 🎯 QUICK DECISION TREE

**"I need to..."**

### → Understand the system

Read: **QUICK_START_GUIDE.md** → **IDE_SYSTEM_CONTEXT.md**

### → Build a new feature (e.g., email inbox, task board)

Read: **IDE_LLM_BUILD_PROMPT.md** (find relevant phase) → **IDE_SYSTEM_CONTEXT.md** (integration patterns)

### → Fix a bug or error

Read: **IDE_AUDIT_PROMPT.md** (Part 1: Error Detection) → **IDE_SYSTEM_CONTEXT.md** (troubleshooting)

### → Improve user experience

Read: **IDE_AUDIT_PROMPT.md** (Part 3: UX Friction) → **IDE_LLM_BUILD_PROMPT.md** (see what's missing)

### → Optimize performance

Read: **IDE_AUDIT_PROMPT.md** (Part 4: Performance) → **IDE_SYSTEM_CONTEXT.md** (data flow)

### → Check security

Read: **IDE_AUDIT_PROMPT.md** (Part 5: Security) → **ARCHITECTURE.md** (security section)

### → Implement Altimeter integration

Read: **IDE_SYSTEM_CONTEXT.md** (integration patterns) → **IDE_LLM_BUILD_PROMPT.md** (Phase 1.3) → **ARCHITECTURE.md** (lines 389-456)

### → Implement AI agent (draft, task, calendar)

Read: **IDE_LLM_BUILD_PROMPT.md** (Phase 2) → **ARCHITECTURE.md** (AI capabilities section) → **IDE_SYSTEM_CONTEXT.md** (Gemini integration)

### → Implement database/API

Read: **ARCHITECTURE.md** (schema) → **IDE_LLM_BUILD_PROMPT.md** (Phase 1.1 or Phase 4.6) → **IDE_SYSTEM_CONTEXT.md** (current state)

---

## 🚀 COMMON WORKFLOWS

### Workflow 1: "I'm new to this project"

1. Read **QUICK_START_GUIDE.md** (5 min)
2. Skim **IDE_SYSTEM_CONTEXT.md** (focus on system overview, port architecture) (10 min)
3. Start services and explore UI
4. Read relevant sections as needed

### Workflow 2: "Build email inbox feature"

1. Read **IDE_LLM_BUILD_PROMPT.md** Phase 4.1 (Email Intelligence Module) (10 min)
2. Read **IDE_SYSTEM_CONTEXT.md** (API endpoints, database schema) (15 min)
3. Read **ARCHITECTURE.md** lines 120-168 (email schema) (5 min)
4. Implement following task checklist
5. Validate with criteria from build prompt

### Workflow 3: "Fix slow email loading"

1. Read **IDE_AUDIT_PROMPT.md** Part 4 (Performance Bottlenecks) (10 min)
2. Run performance audit on email components
3. Identify N+1 queries, large payloads, missing pagination
4. Read **IDE_SYSTEM_CONTEXT.md** (optimization patterns) (5 min)
5. Implement fixes

### Workflow 4: "Improve UX of task board"

1. Read **IDE_AUDIT_PROMPT.md** Part 3 (UX Friction) (15 min)
2. Check for: loading states, error messages, empty states, drag-drop feedback
3. Read **IDE_LLM_BUILD_PROMPT.md** Phase 4.2 (Task Management UI) (10 min)
4. See what's missing vs what should be implemented
5. Add UX improvements

### Workflow 5: "Pre-deployment audit"

1. Read **IDE_AUDIT_PROMPT.md** (skim all 6 parts) (20 min)
2. Run comprehensive audit checklist
3. Generate audit report
4. Fix Critical and High severity issues
5. Validate with **IDE_LLM_BUILD_PROMPT.md** Phase 6 (Testing)

---

## ⚠️ CRITICAL RULES (Never Forget)

### 1. **Port Architecture** (UPDATED)

- Atlas Backend: **4201**
- Atlas Frontend: **4202**
- Altimeter Backend: **4203**
- Altimeter Frontend: **4204**

Old ports (6900, 5173, 5000) are **DEPRECATED**.

### 2. **NEVER Truncate Email Bodies**

From ARCHITECTURE.md:274-308, this is a **CRITICAL** requirement.

- Store full `body_text` and `body_html`
- Archive old emails to `.zip` if needed
- Never delete email content

### 3. **Always Link to Altimeter Projects**

- Emails should auto-link to `project_id` when possible
- Use regex pattern `\d{2}-\d{4}` to detect project numbers
- Query Altimeter contacts to match senders
- Include project context in AI operations

### 4. **Local-First Privacy**

- All data stored locally (SQLite + ChromaDB)
- Only API calls to Google (Gmail, Calendar) and Gemini
- Never send sensitive data to cloud storage
- Encrypt credentials in `config/secrets.json`

### 5. **Construction Domain Context**

This is a **construction project management** system:

- RFI = Request for Information
- Submittal = Product approval documents
- Cost Codes = 600-series electrical work breakdown
- Strata = Permission level (1-5)

---

## 📂 FILE LOCATIONS (Quick Reference)

### Atlas

- Root: `C:\Users\mhkem\.atlas\`
- Backend: `C:\Users\mhkem\.atlas\backend\`
- Frontend: `C:\Users\mhkem\.atlas\frontend\src\`
- Database: `C:\Users\mhkem\OneDrive\Documents\databasedev\atlas.db`
- Config: `C:\Users\mhkem\.atlas\config\secrets.json`

### Altimeter

- Root: `C:\Users\mhkem\.altimeter\`
- Database: `C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db`

### Davis Projects Knowledge Base

- Root: `C:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive\`
- Cost Codes: `.../COST_CODES/`
- Guidelines: `.../GUIDELINES/`
- Skills: `.../SKILLS/`
- Projects: `.../PROJECTS/`

---

## 🛠️ START SERVICES (Quick Commands)

### Terminal 1: Atlas Backend

```bash
cd C:\Users\mhkem\.atlas\backend
.venv\Scripts\activate
python main.py
```

Access: <http://localhost:4201> | API Docs: <http://localhost:4201/docs>

### Terminal 2: Atlas Frontend

```bash
cd C:\Users\mhkem\.atlas\frontend
npm run dev
```

Access: <http://localhost:4202>

---

## 🧪 TESTING COMMANDS

### Backend Tests

```bash
cd C:\Users\mhkem\.atlas\backend
pytest -v
```

### Frontend Tests

```bash
cd C:\Users\mhkem\.atlas\frontend
npm test
```

### Database Inspection

```bash
sqlite3 C:\Users\mhkem\OneDrive\Documents\databasedev\atlas.db
.tables
.schema emails
SELECT COUNT(*) FROM emails;
```

### Altimeter Database Query

```bash
sqlite3 C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db
SELECT * FROM Projects WHERE ProjectID LIKE '25-%';
```

---

## 🆘 TROUBLESHOOTING (Quick Fixes)

### Backend won't start

1. Check virtual environment: `.venv\Scripts\activate`
2. Check port available: `netstat -ano | findstr 4201`
3. Check logs: `data\logs\`

### Frontend API calls fail

1. Verify backend running on 4201
2. Check CORS in `backend/core/config.py`
3. Inspect browser console (F12)

### Altimeter integration broken

1. Verify database path exists
2. Test connection: `sqlite3 [path] .tables`
3. Check `altimeter_service.py` for errors

### Gemini API errors

1. Verify `GEMINI_API_KEY` in `config/secrets.json`
2. Check API quota (<https://aistudio.google.com/>)
3. Check logs for error details

---

## 📊 CURRENT SYSTEM STATE

### ✅ Implemented

- Basic FastAPI backend structure
- React frontend with navigation
- Draft agent (Gemini integration)
- Gmail send functionality
- Knowledge base reading
- Document control workflow
- Altimeter connector (basic)

### ❌ Not Yet Implemented (High Priority)

- Email sync and inbox UI
- Task extraction and management UI
- Calendar integration (Google Calendar sync)
- Vector search (ChromaDB RAG)
- Background scheduler jobs
- Most API endpoints (see IDE_LLM_BUILD_PROMPT.md Phase 4.6)

See **IDE_LLM_BUILD_PROMPT.md** for complete implementation roadmap.

---

## 🎓 LEARNING PATH

### Day 1: Orientation

- Read **QUICK_START_GUIDE.md**
- Read **IDE_SYSTEM_CONTEXT.md** (system overview)
- Start services and explore UI
- Run backend tests to see what's working

### Day 2: Deep Dive

- Read **ARCHITECTURE.md** (full spec)
- Read **IDE_LLM_BUILD_PROMPT.md** (critical path)
- Understand database schema
- Understand integration patterns

### Day 3: Build/Audit

- Choose: Build new feature OR audit existing code
- **Build**: Use **IDE_LLM_BUILD_PROMPT.md**
- **Audit**: Use **IDE_AUDIT_PROMPT.md**
- Reference **IDE_SYSTEM_CONTEXT.md** as needed

---

## 📞 GETTING HELP

### When stuck

1. Check **IDE_SYSTEM_CONTEXT.md** troubleshooting section
2. Review **ARCHITECTURE.md** for design intent
3. Check **IDE_AUDIT_PROMPT.md** for common issues
4. Search all docs with Ctrl+F for keywords

### Error messages

1. Read **IDE_AUDIT_PROMPT.md** Part 1 (Error Detection)
2. Check backend logs: `data/logs/`
3. Check browser console (F12)

### Design questions

1. Consult **ARCHITECTURE.md** (authoritative)
2. Check **IDE_SYSTEM_CONTEXT.md** (implementation patterns)

---

## ✅ FINAL CHECKLIST BEFORE YOU START

- [ ] I know which document to read for my task (see decision tree above)
- [ ] I understand the port architecture (4201/4202/4203/4204)
- [ ] I know the critical rule: NEVER truncate email bodies
- [ ] I know where Atlas, Altimeter, and Davis Projects are located
- [ ] I can start the services (backend on 4201, frontend on 4202)
- [ ] I know how to troubleshoot common issues

---

**You're ready! Pick your task, read the relevant documentation, and start building/auditing.**

**Questions? Refer back to this README to find the right documentation.**

---

**Last Updated**: 2026-01-25
**Status**: Port migration complete, documentation ready for IDE LLMs
