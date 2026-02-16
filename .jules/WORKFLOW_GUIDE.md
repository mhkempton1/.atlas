# Jules Collaboration Workflow Guide
**How to efficiently delegate work to Jules and have Claude validate it**

---

## 🔄 **The Complete Workflow**

### **Phase 1: Task Preparation (Claude)**
```
You: "Claude, prepare Task X for Jules"

Claude does:
1. ✅ Creates detailed prompt in TASK_QUEUE.md
2. ✅ Lists all files to create/modify
3. ✅ Specifies acceptance criteria
4. ✅ Identifies dependencies
5. ✅ Generates validation checklist
6. ✅ Marks task as "📋 Ready for Jules"
```

### **Phase 2: Task Delegation (You → Jules)**
```
You:
1. Open .jules/TASK_QUEUE.md
2. Find the task marked "📋 Ready for Jules"
3. Copy entire "Prompt for Jules" section
4. Go to jules.google.com
5. Paste prompt and send
6. Update TASK_QUEUE.md: Change status to "🔄 In Progress"
7. Note start date
```

### **Phase 3: Jules Works**
```
Jules:
1. Creates branch (e.g., altimeter-bidirectional-sync)
2. Implements features per prompt
3. Commits incrementally with clear messages
4. Pushes to GitHub when phase/task complete
5. (Optional) Comments in GitHub PR with summary
```

### **Phase 4: Validation (Claude)**
```
You: "Claude, Jules pushed Task X to branch Y, please validate"

Claude does:
1. ✅ Pulls latest from GitHub branch
2. ✅ Checks all files created/modified
3. ✅ Runs validation checklist
4. ✅ Tests imports and basic functionality
5. ✅ Reviews code quality and patterns
6. ✅ Identifies any issues
7. ✅ Updates TASK_QUEUE.md with results
```

### **Phase 5A: If Validation Passes**
```
Claude:
1. ✅ Merges branch to master
2. ✅ Marks task "✅ Complete" in TASK_QUEUE.md
3. ✅ Updates progress tracking
4. ✅ Identifies next task to delegate

You:
1. Review Claude's summary
2. Test in local environment if desired
3. Move to next task in queue
```

### **Phase 5B: If Validation Fails**
```
Claude:
1. ❌ Documents specific issues found
2. ❌ Creates feedback prompt for Jules
3. ❌ Keeps task status "🔄 In Progress - Needs Fixes"

You:
1. Copy Claude's feedback prompt
2. Send to Jules with issues to fix
3. Jules fixes and re-pushes
4. Return to Phase 4 (Claude validates again)
```

---

## 📋 **Example: Complete Task Flow**

### **Task: Build Altimeter Bidirectional Sync**

#### **Day 1 Morning** - Task Preparation
```
You: "Claude, I need Jules to build real-time Altimeter sync. Prepare the task."

Claude:
- Creates detailed prompt in TASK_QUEUE.md
- Specifies 7-day timeline broken into phases
- Lists 10+ files to create/modify
- Defines acceptance criteria
- Marks task "📋 Ready for Jules"
- Saves: "Task 1 ready. Copy prompt from TASK_QUEUE.md and send to Jules."
```

#### **Day 1 Afternoon** - Delegation
```
You:
1. Open .jules/TASK_QUEUE.md
2. Copy "Prompt for Jules" for Task 1
3. Send to jules.google.com
4. Update TASK_QUEUE.md: "🔄 In Progress, Started: 2026-02-15"
```

#### **Day 1-2** - Jules Works (Phase 1)
```
Jules:
- Creates branch: altimeter-bidirectional-sync
- Implements database schema + sync queue service
- Commits: "feat: add sync queue database schema and service"
- Pushes to GitHub
```

#### **Day 3 Morning** - Validation (Phase 1)
```
You: "Claude, Jules pushed Phase 1 of Task 1, please validate"

Claude:
1. Pulls branch altimeter-bidirectional-sync
2. Checks:
   ✅ migrate_add_sync_queue.py created
   ✅ altimeter_sync_service.py created
   ✅ Database migration runs without errors
   ✅ Sync queue logic follows existing patterns
   ✅ Type hints present
   ⚠️  Issue: Missing error handling in retry logic
   ⚠️  Issue: sync_status enum not defined in models.py

3. Creates feedback for Jules:
   "Phase 1 is 95% complete. Two issues to fix:
   1. Add try/except in altimeter_sync_service.py line 45
   2. Define sync_status enum in database/models.py
   Please fix and re-push."

4. Updates TASK_QUEUE.md: "🔄 In Progress - Needs Fixes"
```

#### **Day 3 Afternoon** - Jules Fixes
```
You: Copy Claude's feedback, send to Jules

Jules:
- Fixes both issues
- Commits: "fix: add error handling and sync_status enum"
- Pushes to GitHub
```

#### **Day 3 Evening** - Re-validation
```
You: "Claude, Jules re-pushed Phase 1 fixes, validate again"

Claude:
1. Pulls latest
2. Checks:
   ✅ All issues resolved
   ✅ Error handling added
   ✅ Enum defined correctly
   ✅ Tests pass

3. Approves Phase 1
4. Updates TASK_QUEUE.md: "Phase 1 ✅ Complete, ready for Phase 2"
```

#### **Day 4-5** - Phases 2-3 (same workflow)

#### **Day 7** - Task Complete
```
Claude:
1. Validates final phase
2. Runs full integration test
3. ✅ Merges altimeter-bidirectional-sync → master
4. ✅ Marks Task 1 "✅ Complete" in TASK_QUEUE.md
5. ✅ Pushes to origin/master
6. Reports: "Task 1 complete and deployed. Ready for Task 2."
```

---

## 🎯 **Quick Reference Commands**

### **For You to Say to Claude:**

| What You Want | What to Say |
|---------------|-------------|
| Prepare new task | "Claude, prepare [description] for Jules" |
| Validate Jules' work | "Claude, Jules pushed [task] to branch [name], validate" |
| Check task status | "Claude, show TASK_QUEUE status" |
| Get next task | "Claude, what's the next task for Jules?" |
| Review issues | "Claude, review validation issues for Task X" |
| Create feedback | "Claude, create feedback prompt for Jules on Task X" |

### **Files Claude Maintains:**

| File | Purpose |
|------|---------|
| `.jules/TASK_QUEUE.md` | Master task list with prompts |
| `.jules/VALIDATION_LOG.md` | History of all validations |
| `.jules/FEEDBACK_TEMPLATES.md` | Reusable feedback patterns |

---

## 🚀 **Optimization Tips**

### **Parallel Task Execution**
```
If two tasks don't touch the same files, Jules can work on both:

Task 1: Altimeter Sync (backend/services/altimeter_*)
Task 2: Service Layer (backend/services/task_service.py)

These are independent → send both to Jules, she works in parallel branches
```

### **Incremental Commits**
```
Tell Jules: "Commit after each file/feature, don't wait for entire task"

Benefits:
- Claude can validate sooner
- Easier to identify issues
- Safer rollback if needed
```

### **Phase-Based Approval**
```
For large tasks (1+ week), break into phases:

Task 1 Phase 1: Database schema (Days 1-2)
Task 1 Phase 2: API endpoints (Days 3-4)
Task 1 Phase 3: Frontend integration (Days 5-6)
Task 1 Phase 4: Testing (Day 7)

Validate and approve each phase before Jules continues.
Prevents wasted work if early phase has issues.
```

---

## 🔍 **What Claude Checks During Validation**

### **Code Quality**
- ✅ Follows existing patterns in codebase
- ✅ Type hints on all functions/methods
- ✅ Docstrings for public APIs
- ✅ Error handling (try/except where needed)
- ✅ No hardcoded values (uses config)
- ✅ Consistent naming conventions

### **Functionality**
- ✅ All required files created
- ✅ Imports work (no ModuleNotFoundError)
- ✅ Database migrations run cleanly
- ✅ API endpoints return expected responses
- ✅ Frontend components render without errors

### **Testing**
- ✅ Unit tests written for new code
- ✅ Integration tests for critical paths
- ✅ Existing tests still pass
- ✅ Test coverage >80% for new code

### **Security**
- ✅ No SQL injection vulnerabilities
- ✅ Input validation present
- ✅ Authentication/authorization checks
- ✅ No sensitive data in logs
- ✅ API keys in environment variables

### **Performance**
- ✅ No N+1 query problems
- ✅ Database indexes on filtered columns
- ✅ Async/await used correctly
- ✅ No unnecessary loops or nested queries

---

## 📊 **Tracking Progress**

Claude maintains a validation log:

```markdown
# Validation Log

## 2026-02-15 - Task 1 Phase 1 Validation
**Branch**: altimeter-bidirectional-sync
**Validator**: Claude
**Status**: ⚠️ Needs Fixes

Files Checked:
- ✅ backend/services/altimeter_sync_service.py (good)
- ✅ backend/migrate_add_sync_queue.py (good)
- ⚠️ backend/database/models.py (missing enum)

Issues:
1. sync_status enum not defined (line 45 reference fails)
2. Error handling missing in retry logic

Feedback sent to Jules: [link to prompt]

## 2026-02-15 - Task 1 Phase 1 Re-validation
**Branch**: altimeter-bidirectional-sync
**Validator**: Claude
**Status**: ✅ Approved

All issues resolved. Phase 1 complete.
```

---

## ⚡ **Speeding Things Up**

### **Use Templates**
Claude can save common prompts:

```
You: "Claude, use the 'service class' template for CalendarService"

Claude:
- Loads template from .jules/templates/
- Fills in CalendarService specifics
- Creates ready-to-send prompt
- Faster than writing from scratch each time
```

### **Batch Validation**
```
You: "Claude, Jules pushed 3 tasks today, validate all"

Claude:
- Validates Task 1, 2, 3 in sequence
- Creates combined report
- You review once instead of 3 times
```

### **Auto-Merge (Risky but Fast)**
```
You: "Claude, if validation passes with zero issues, auto-merge to master"

Claude:
- Validates as usual
- If perfect → merges automatically
- If any issues → stops and asks you
- Use for small/safe changes only
```

---

## 🎓 **Training Jules**

Over time, Jules learns your codebase patterns. Help her by:

### **Providing Examples**
```
In prompt: "Follow the pattern from task_routes.py lines 45-60"
Better than: "Use dependency injection"
```

### **Referencing Existing Code**
```
In prompt: "Create EmailService similar to existing AltimeterService"
Jules can read AltimeterService and mimic the pattern
```

### **Incremental Complexity**
```
Task 1: Simple CRUD service (learn patterns)
Task 2: Service with external API calls (build on Task 1)
Task 3: Service with async/queue (build on Task 2)

Each task builds on previous knowledge
```

---

## 🆘 **Troubleshooting**

### **If Jules Misunderstands Prompt**
```
Problem: Jules implemented wrong approach

Solution:
1. Claude identifies issue in validation
2. You create clarification prompt:
   "Jules, the requirement was X, but you implemented Y.
   Please change to X following this example: [code]"
3. Jules fixes
4. Re-validate
```

### **If Validation Takes Too Long**
```
Problem: Claude takes 30+ min to validate

Solution:
1. Break task into smaller phases
2. Validate each phase separately
3. Use "quick validation" mode:
   "Claude, quick check - do imports work and tests pass?"
   (Skips deep code review, just checks basics)
```

### **If Tasks Keep Failing Validation**
```
Problem: Jules fails validation 3+ times on same task

Solution:
1. Prompt might be unclear
2. Task might be too complex
3. Claude creates "debugging session" prompt:
   "Jules, let's debug together. Show me your approach for X"
4. Jules explains her logic
5. You/Claude identify disconnect
6. Refine prompt and try again
```

---

## 📅 **Recommended Schedule**

### **Weekly Sprint Example**

**Monday**: Planning
- Claude prepares 2-3 tasks for week
- You review and prioritize
- Send Task 1 to Jules

**Tuesday-Thursday**: Execution
- Jules works on tasks
- Claude validates incrementally
- You provide direction on issues

**Friday**: Review & Integration
- Final validation of week's work
- Merge approved tasks to master
- Plan next week's tasks

---

**This workflow lets you delegate to Jules efficiently while Claude ensures quality. You're the orchestrator, Claude is quality control, Jules is execution.**

Ready to start? Say: "Claude, prepare Task 1 for Jules"
