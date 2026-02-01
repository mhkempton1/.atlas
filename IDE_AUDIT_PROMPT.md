# ATLAS SYSTEM AUDIT PROMPT FOR IDE LLM

## Mission: Identify Issues, Incomplete Implementations, and UX Friction

When auditing the Atlas system, systematically analyze the codebase to find:

1. **Errors and Bugs** - Code that will fail at runtime
2. **Incomplete Implementations** - Stub functions, TODOs, missing integrations
3. **UX Friction Points** - User interface pain points and usability issues
4. **Performance Bottlenecks** - Slow operations, inefficient queries
5. **Security Vulnerabilities** - Exposed secrets, injection risks, auth gaps
6. **Integration Gaps** - Broken Atlas ↔ Altimeter connections

---

## PART 1: ERROR DETECTION

### What to Look For

#### Backend Errors (Python/FastAPI)

- [ ] **Import errors**: Missing modules, incorrect import paths
- [ ] **Type mismatches**: Function arguments not matching types
- [ ] **Database errors**:
  - Queries to non-existent tables/columns
  - Missing foreign key constraints
  - Transactions without rollback
- [ ] **API route errors**:
  - Missing Pydantic models for request/response
  - Incorrect HTTP methods (GET vs POST)
  - Missing error handling (try/except)
  - Unhandled exceptions returning 500
- [ ] **Service errors**:
  - Hardcoded paths that don't exist
  - API calls without timeout handling
  - File operations without error checking
  - Missing null/None checks

#### Frontend Errors (React/JavaScript)

- [ ] **Console errors**: Check browser console for warnings/errors
- [ ] **API call errors**:
  - Incorrect endpoint URLs
  - Missing error handling (.catch())
  - No loading states during async operations
  - Unhandled promise rejections
- [ ] **Component errors**:
  - Missing prop validation
  - State updates on unmounted components
  - Infinite render loops (useEffect without dependencies)
  - Memory leaks (uncleared intervals/timeouts)
- [ ] **Build errors**:
  - Missing dependencies in package.json
  - Import errors (wrong paths, case sensitivity)
  - Unused imports causing warnings

#### Integration Errors

- [ ] **Altimeter connection**:
  - Database path incorrect or inaccessible
  - SQL queries with wrong table/column names
  - Missing error handling for DB connection failures
- [ ] **Gmail API**:
  - Missing OAuth credentials
  - Invalid API scopes
  - Rate limit handling missing
  - Token refresh not implemented
- [ ] **Gemini API**:
  - Missing API key validation
  - No fallback when API fails
  - Unhandled API errors (quota exceeded, invalid request)

### Audit Commands

```bash
# Backend: Check for import errors
cd C:\Users\mhkem\.atlas\backend
python -m py_compile core/app.py
python -m py_compile services/*.py
python -m py_compile agents/*.py

# Backend: Check for syntax errors
python -m pylint backend/ --errors-only

# Frontend: Check for build errors
cd C:\Users\mhkem\.atlas\frontend
npm run build

# Frontend: Check for lint errors
npm run lint

# Test database connection
sqlite3 C:\Users\mhkem\OneDrive\Documents\databasedev\atlas.db ".schema"
sqlite3 C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db ".schema"
```

### Error Reporting Format

```markdown
## ERROR: [Error Type]
**File**: `path/to/file.py:line_number`
**Severity**: Critical | High | Medium | Low
**Description**: Clear explanation of the error
**Impact**: What breaks when this error occurs
**Fix**: Specific code changes needed

**Example**:
## ERROR: Missing Import
**File**: `backend/services/gmail_service.py:15`
**Severity**: Critical
**Description**: `from google.oauth2.credentials import Credentials` is missing
**Impact**: Gmail service cannot authenticate, all email sync fails
**Fix**: Add `from google.oauth2.credentials import Credentials` at top of file
```

---

## PART 2: INCOMPLETE IMPLEMENTATIONS

### What to Look For

#### Stub Functions (Needs Implementation)

Search for these patterns:

```python
# Python
def function_name():
    pass

def function_name():
    raise NotImplementedError

def function_name():
    # TODO: implement this
    return None
```

```javascript
// JavaScript
function functionName() {
  // TODO: implement
  return null;
}

const functionName = () => {
  throw new Error('Not implemented');
};
```

#### Missing Database Tables

- [ ] Compare ARCHITECTURE.md schema (lines 120-272) with actual database
- [ ] Check if all tables exist: `sqlite3 atlas.db ".tables"`
- [ ] Verify foreign key constraints
- [ ] Check if indexes are created

#### Missing API Endpoints

Compare `IDE_LLM_BUILD_PROMPT.md` Phase 4.6 required endpoints with `api/routes.py`:

**Required but Missing**:

- [ ] Email CRUD: `/api/v1/email/list`, `/api/v1/email/{email_id}`, `/api/v1/email/sync`
- [ ] Task CRUD: `/api/v1/tasks/*` (all endpoints)
- [ ] Calendar CRUD: `/api/v1/calendar/*` (all endpoints)
- [ ] AI endpoints: `/api/v1/ai/chat`, `/api/v1/ai/search`
- [ ] Settings endpoints: `/api/v1/settings/*`

#### Missing UI Components

Compare `App.jsx` navigation with implemented components:

**Declared but Missing/Incomplete**:

- [ ] `EmailList.jsx` - Inbox view (not in components/email/)
- [ ] `EmailView.jsx` - Single email display
- [ ] `ThreadView.jsx` - Conversation threads
- [ ] `TaskList.jsx` - Task list view
- [ ] `TaskBoard.jsx` - Kanban board
- [ ] `TaskDetail.jsx` - Task detail modal
- [ ] `CalendarView.jsx` - Calendar component
- [ ] `EventDetail.jsx` - Event modal
- [ ] `MeetingScheduler.jsx` - Smart scheduling

#### Missing Services/Integrations

- [ ] **ChromaDB**: `search_service.py` - Vector search not implemented
- [ ] **Calendar Agent**: `calendar_agent.py` - Not implemented
- [ ] **Project Agent**: `project_agent.py` - Not implemented
- [ ] **Task Agent**: `task_agent.py` - Exists but minimal implementation
- [ ] **Background Scheduler**: `scheduler_service.py` - Exists but jobs not defined

### Audit Commands

```bash
# Find TODO comments
cd C:\Users\mhkem\.atlas
grep -r "TODO" backend/ frontend/src/

# Find NotImplementedError
grep -r "NotImplementedError" backend/

# Find pass statements in functions
grep -A 2 "def " backend/**/*.py | grep "pass"

# Check database tables
sqlite3 C:\Users\mhkem\.atlas\data\databases\atlas.db ".tables"

# List all API routes
curl http://localhost:4201/docs
```

### Incomplete Implementation Reporting Format

```markdown
## INCOMPLETE: [Feature Name]
**Location**: `path/to/file`
**Status**: Stub | Partial | Missing
**Required By**: [Which feature depends on this]
**Priority**: Critical | High | Medium | Low
**Implementation Needed**: Detailed description

**Example**:
## INCOMPLETE: Email Sync Service
**Location**: `backend/services/gmail_service.py`
**Status**: Partial (only send implemented, sync missing)
**Required By**: Email inbox UI, task extraction, draft generation with context
**Priority**: Critical
**Implementation Needed**:
- OAuth 2.0 authentication flow
- sync_emails() function to fetch from Gmail API
- Email parsing (headers, body, attachments)
- Save to database with full body preservation
- Call altimeter_service for project linking
```

---

## PART 3: UX FRICTION ANALYSIS

### Frontend User Experience Issues

#### 1. **Loading States Missing**

Check every API call for loading feedback:

```javascript
// BAD: No loading state
const handleClick = async () => {
  const data = await api.getData();
  setData(data);
};

// GOOD: With loading state
const [isLoading, setIsLoading] = useState(false);
const handleClick = async () => {
  setIsLoading(true);
  try {
    const data = await api.getData();
    setData(data);
  } finally {
    setIsLoading(false);
  }
};
```

**Audit**:

- [ ] Every button with async action has loading spinner
- [ ] API calls show loading indicator
- [ ] Disable buttons during loading to prevent double-click

#### 2. **Error Messages Missing/Unclear**

```javascript
// BAD: No user feedback
try {
  await api.sendEmail(data);
} catch (error) {
  console.error(error); // User sees nothing!
}

// GOOD: User-friendly error
try {
  await api.sendEmail(data);
  showToast('Email sent successfully', 'success');
} catch (error) {
  showToast('Failed to send email: ' + error.message, 'error');
}
```

**Audit**:

- [ ] All errors shown to user (toast/alert/modal)
- [ ] Error messages are clear, not technical jargon
- [ ] Suggest corrective action ("Check your internet connection")

#### 3. **Empty States Missing**

```javascript
// BAD: Shows nothing when empty
{emails.map(email => <EmailItem email={email} />)}

// GOOD: Empty state message
{emails.length === 0 ? (
  <div className="empty-state">
    <Mail className="w-12 h-12 text-gray-400" />
    <p>No emails found</p>
    <button onClick={syncEmails}>Sync Now</button>
  </div>
) : (
  emails.map(email => <EmailItem email={email} />)
)}
```

**Audit**:

- [ ] Every list has empty state (emails, tasks, calendar, files)
- [ ] Empty state includes helpful action (sync, create, search)
- [ ] Visual feedback (icon + message)

#### 4. **Navigation Confusion**

**Audit**:

- [ ] Clear visual indication of current page (active state in sidebar)
- [ ] Breadcrumbs for nested pages
- [ ] Back button where needed (email detail → inbox)
- [ ] Consistent navigation patterns
- [ ] Mobile menu accessible (hamburger works)

#### 5. **Form Validation Missing**

```javascript
// BAD: No validation
const handleSubmit = () => {
  api.createTask({ title: taskTitle });
};

// GOOD: Validation with feedback
const handleSubmit = () => {
  if (!taskTitle.trim()) {
    setError('Title is required');
    return;
  }
  if (taskTitle.length > 200) {
    setError('Title must be less than 200 characters');
    return;
  }
  api.createTask({ title: taskTitle });
};
```

**Audit**:

- [ ] Required fields marked with asterisk
- [ ] Real-time validation (on blur or on change)
- [ ] Clear error messages next to fields
- [ ] Submit button disabled until valid

#### 6. **No Feedback on Actions**

**Audit**:

- [ ] Success toasts after create/update/delete
- [ ] Confirmation dialogs before destructive actions (delete, archive)
- [ ] Optimistic UI updates (task marked done before API confirms)
- [ ] Undo option for reversible actions

#### 7. **Poor Data Presentation**

**Audit**:

- [ ] Dates formatted consistently (e.g., "2 hours ago", "Jan 25, 2026")
- [ ] Long text truncated with "..." and expand option
- [ ] Email addresses shown as names when contact exists
- [ ] Project IDs shown as project names with tooltip for ID
- [ ] Color coding for status (urgent=red, normal=blue, done=green)

#### 8. **Slow Perceived Performance**

**Audit**:

- [ ] Skeleton loaders for slow-loading content
- [ ] Pagination for long lists (>50 items)
- [ ] Lazy loading for images/attachments
- [ ] Debounced search (wait 300ms after typing)
- [ ] Cached API responses (don't re-fetch on every navigation)

#### 9. **Accessibility Issues**

**Audit**:

- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Focus states visible (blue outline on focused elements)
- [ ] Alt text on images
- [ ] ARIA labels on icon-only buttons
- [ ] Color contrast meets WCAG standards (test with tool)
- [ ] Screen reader friendly (semantic HTML)

#### 10. **Mobile Responsiveness**

**Audit**:

- [ ] Sidebar collapses to hamburger on mobile
- [ ] Tables scroll horizontally or stack vertically
- [ ] Touch targets at least 44x44px
- [ ] Font sizes readable on mobile (≥16px)
- [ ] No horizontal scroll on any page

### UX Friction Reporting Format

```markdown
## UX FRICTION: [Issue Name]
**Component**: `ComponentName.jsx`
**Category**: Loading | Errors | Empty State | Navigation | Forms | Feedback | Data Display | Performance | Accessibility | Mobile
**User Impact**: What frustration does this cause?
**Frequency**: How often will users encounter this?
**Fix**: Specific UI/UX changes needed

**Example**:
## UX FRICTION: No Loading State on Email Send
**Component**: `ComposeDraft.jsx`
**Category**: Loading
**User Impact**: User clicks "Send" but gets no feedback. They don't know if it's working, so they click again, sending duplicate emails.
**Frequency**: Every email send (dozens per day)
**Fix**:
1. Add `const [isSending, setIsSending] = useState(false);`
2. Show spinner on button: `<button disabled={isSending}>{isSending ? <Spinner /> : 'Send'}</button>`
3. Disable button during send
4. Show success toast after send
```

---

## PART 4: PERFORMANCE BOTTLENECKS

### What to Look For

#### Backend Performance

- [ ] **N+1 Query Problem**: Loop calling database for each item

  ```python
  # BAD
  for email in emails:
      project = db.query(Project).filter_by(id=email.project_id).first()

  # GOOD
  emails = db.query(Email).options(joinedload(Email.project)).all()
  ```

- [ ] **Missing Indexes**: Queries on unindexed columns

  ```python
  # Check if email.project_id has index
  # Add if missing: CREATE INDEX idx_email_project_id ON emails(project_id);
  ```

- [ ] **Inefficient Vector Search**: Searching entire collection without filters

  ```python
  # BAD: Search all 10,000 emails
  results = chroma_collection.query(query_texts=[query], n_results=10)

  # GOOD: Filter by project first
  results = chroma_collection.query(
      query_texts=[query],
      n_results=10,
      where={'project_id': '25-0308'}
  )
  ```

- [ ] **Large Payloads**: Returning full email bodies in list endpoints

  ```python
  # BAD: Returns 50 emails with full bodies (huge JSON)
  @app.get("/emails")
  def get_emails():
      return db.query(Email).limit(50).all()

  # GOOD: Return snippets only
  @app.get("/emails")
  def get_emails():
      return db.query(Email.id, Email.subject, Email.snippet).limit(50).all()
  ```

- [ ] **Synchronous External API Calls**: Blocking requests

  ```python
  # BAD: Blocks until Gemini responds (5+ seconds)
  def generate_draft(email):
      draft = gemini.generate_content(prompt)  # Synchronous
      return draft

  # GOOD: Background job
  def generate_draft(email):
      task_id = scheduler.enqueue(gemini_generate, email)
      return {"task_id": task_id, "status": "processing"}
  ```

#### Frontend Performance

- [ ] **Unnecessary Re-renders**: Components re-rendering on every state change

  ```javascript
  // Use React.memo for expensive components
  export default React.memo(EmailList);

  // Use useMemo for expensive calculations
  const filteredEmails = useMemo(() =>
    emails.filter(e => e.category === 'work'),
    [emails]
  );
  ```

- [ ] **Large Lists Without Virtualization**: Rendering 1000+ items

  ```javascript
  // BAD: Renders all 1000 emails (slow scroll)
  {emails.map(email => <EmailItem email={email} />)}

  // GOOD: Use react-window or pagination
  import { FixedSizeList } from 'react-window';
  ```

- [ ] **No Request Debouncing**: API called on every keystroke

  ```javascript
  // BAD: Calls API on every letter typed
  <input onChange={(e) => searchEmails(e.target.value)} />

  // GOOD: Debounce 300ms
  const debouncedSearch = useDebouncedCallback(searchEmails, 300);
  <input onChange={(e) => debouncedSearch(e.target.value)} />
  ```

- [ ] **Bundle Size**: Check for large dependencies

  ```bash
  npm run build
  # Check output size - should be <500KB gzipped
  # Use webpack-bundle-analyzer to find large imports
  ```

### Performance Audit Commands

```bash
# Backend: Profile slow endpoints
# Add @profile decorator to functions, run with profiler

# Frontend: Lighthouse audit
# Open Chrome DevTools > Lighthouse > Run audit

# Database: Query performance
sqlite3 atlas.db
EXPLAIN QUERY PLAN SELECT * FROM emails WHERE project_id = '25-0308';

# Network: Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:4201/api/v1/emails
```

### Performance Issue Reporting Format

```markdown
## PERFORMANCE: [Issue Name]
**Location**: `file.py` or `Component.jsx`
**Issue**: Description of bottleneck
**Impact**: Slow page load | API timeout | High memory | Database lock
**Measurement**: Current: X seconds/MB, Target: Y seconds/MB
**Fix**: Optimization strategy

**Example**:
## PERFORMANCE: Slow Email List Load
**Location**: `frontend/src/components/email/EmailList.jsx`
**Issue**: Rendering 500 emails on initial load, takes 3+ seconds
**Impact**: Slow page load, janky scrolling
**Measurement**: Current: 3.2s to interactive, Target: <1s
**Fix**:
1. Implement pagination (50 emails per page)
2. Use react-window for virtualization
3. Backend: Return snippets only, not full bodies
```

---

## PART 5: SECURITY VULNERABILITIES

### What to Look For

#### 1. **Exposed Secrets**

```bash
# Search for hardcoded secrets
cd C:\Users\mhkem\.atlas
grep -r "api_key.*=.*\"sk-" .
grep -r "password.*=.*\"" .
grep -r "AIzaSy" .  # Google API keys

# Check if secrets.json is gitignored
cat .gitignore | grep secrets.json
```

**Audit**:

- [ ] No API keys in code (use environment variables)
- [ ] `secrets.json` in `.gitignore`
- [ ] No passwords in logs
- [ ] Credentials encrypted at rest

#### 2. **SQL Injection Risk**

```python
# BAD: User input directly in query
project_id = request.args.get('project_id')
db.execute(f"SELECT * FROM emails WHERE project_id = '{project_id}'")

# GOOD: Parameterized query
db.query(Email).filter_by(project_id=project_id).all()
```

**Audit**:

- [ ] All database queries use ORM or parameterized queries
- [ ] No f-strings with user input in SQL

#### 3. **XSS (Cross-Site Scripting)**

```javascript
// BAD: Rendering raw HTML from user/email
<div dangerouslySetInnerHTML={{__html: email.body}} />

// GOOD: Sanitize HTML first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(email.body)}} />
```

**Audit**:

- [ ] Email HTML sanitized before rendering
- [ ] User inputs escaped
- [ ] No `eval()` or `innerHTML` with user data

#### 4. **Missing Authentication**

**Audit**:

- [ ] API endpoints require authentication (JWT/session)
- [ ] Sensitive routes protected (settings, system health)
- [ ] CORS configured correctly (not allow-all origins)
- [ ] No admin functions accessible without auth

#### 5. **File Upload Vulnerabilities**

**Audit**:

- [ ] File upload size limits enforced
- [ ] File type validation (whitelist, not blacklist)
- [ ] Uploaded files scanned for malware
- [ ] Files stored outside web root
- [ ] No code execution from upload directory

### Security Audit Commands

```bash
# Check for secrets in code
git grep -i "password\|api_key\|secret"

# Check CORS settings
curl -H "Origin: http://evil.com" http://localhost:4201/api/v1/emails

# Check authentication
curl http://localhost:4201/api/v1/settings/user
# Should return 401 Unauthorized if not logged in
```

### Security Issue Reporting Format

```markdown
## SECURITY: [Vulnerability Type]
**Location**: `file:line`
**Severity**: Critical | High | Medium | Low
**Vulnerability**: OWASP category (XSS, SQL Injection, etc.)
**Exploit Scenario**: How an attacker could exploit this
**Fix**: Security mitigation

**Example**:
## SECURITY: Email HTML Rendering XSS
**Location**: `frontend/src/components/email/EmailView.jsx:45`
**Severity**: High
**Vulnerability**: Cross-Site Scripting (XSS)
**Exploit Scenario**: Attacker sends email with `<script>alert(document.cookie)</script>` in body. When victim opens email in Atlas, script executes and steals session cookies.
**Fix**:
1. Install DOMPurify: `npm install dompurify`
2. Sanitize HTML: `DOMPurify.sanitize(email.body_html)`
3. Remove dangerous tags: `<script>`, `<iframe>`, `onclick` attributes
```

---

## PART 6: INTEGRATION GAPS

### Atlas ↔ Altimeter Integration

#### Missing Bidirectional Sync

**Audit**:

- [ ] Emails link to Altimeter projects (email.project_id populated)
- [ ] Project context fetched when generating drafts
- [ ] Tasks sync to Altimeter daily logs
- [ ] Calendar events created from Altimeter milestones
- [ ] Contact matching (email sender → Altimeter customer/vendor)

#### Broken Integration Points

```python
# Check if Altimeter DB accessible
import sqlite3
try:
    conn = sqlite3.connect(r"C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Altimeter tables:", tables)
except Exception as e:
    print("ERROR: Cannot connect to Altimeter DB:", e)

# Check if project linking works
from services.altimeter_service import altimeter_service
test_email = {"subject": "RE: Project 25-0308 Electrical", "from": "contractor@example.com"}
project_id = altimeter_service.link_email_to_project(test_email)
print("Linked to project:", project_id)  # Should return '25-0308'
```

**Audit**:

- [ ] Altimeter database path correct in config
- [ ] Altimeter tables exist (Projects, Customers, Vendors, DailyLogs)
- [ ] Queries use correct Altimeter schema
- [ ] Error handling if Altimeter DB unavailable

### Atlas ↔ Gmail Integration

**Audit**:

- [ ] OAuth 2.0 credentials configured
- [ ] Gmail API scopes correct (gmail.readonly, gmail.send)
- [ ] Token refresh implemented
- [ ] Rate limiting respected (250 quota units/second)
- [ ] Sync resumes from last sync timestamp
- [ ] Attachments downloaded and stored

### Atlas ↔ Google Calendar Integration

**Audit**:

- [ ] OAuth 2.0 credentials configured
- [ ] Calendar API scopes correct
- [ ] Multiple calendars supported (work + personal)
- [ ] Bidirectional sync (Atlas → Calendar, Calendar → Atlas)
- [ ] Conflict detection works

### Integration Gap Reporting Format

```markdown
## INTEGRATION GAP: [Missing Integration]
**Systems**: Atlas ↔ Altimeter | Atlas ↔ Gmail | Atlas ↔ Calendar
**Expected Behavior**: What should happen
**Current Behavior**: What actually happens (or doesn't)
**Impact**: What feature is broken
**Fix**: Implementation steps

**Example**:
## INTEGRATION GAP: Email-to-Project Linking Not Working
**Systems**: Atlas ↔ Altimeter
**Expected Behavior**: When email with subject "Project 25-0308 RFI" arrives, Atlas should set `email.project_id = '25-0308'` by querying Altimeter
**Current Behavior**: `email.project_id` is always NULL
**Impact**: Draft agent has no project context, tasks not linked to projects, dashboard shows no project activity
**Fix**:
1. Implement `altimeter_service.link_email_to_project(email)`
2. Regex search subject/body for pattern `\d{2}-\d{4}`
3. Query Altimeter: `SELECT ProjectID FROM Projects WHERE ProjectID = ?`
4. Update email record: `email.project_id = project_id`
```

---

## COMPREHENSIVE AUDIT CHECKLIST

Run through this checklist systematically:

### Backend Audit

- [ ] All Python files compile without errors
- [ ] All imports resolve correctly
- [ ] Database schema matches ARCHITECTURE.md
- [ ] All API endpoints have error handling
- [ ] All API endpoints return proper status codes
- [ ] All services have null/None checks
- [ ] All external API calls have timeouts
- [ ] Altimeter integration works (test with real project)
- [ ] Gmail integration works (test with real email)
- [ ] Gemini API calls work (test draft generation)
- [ ] Vector search works (test semantic search)
- [ ] Background jobs scheduled correctly
- [ ] Logs written to `data/logs/`
- [ ] Secrets loaded from `config/secrets.json`
- [ ] No secrets hardcoded in code

### Frontend Audit

- [ ] Build completes without errors (`npm run build`)
- [ ] No console errors in browser
- [ ] All API calls have error handling
- [ ] All API calls have loading states
- [ ] All forms have validation
- [ ] All lists have empty states
- [ ] All actions have user feedback (toasts/alerts)
- [ ] Navigation works (all links clickable)
- [ ] Mobile responsive (test at 375px width)
- [ ] Keyboard navigation works
- [ ] Color contrast passes WCAG AA
- [ ] Images have alt text
- [ ] Performance: Lighthouse score >90

### Integration Audit

- [ ] Emails sync from Gmail
- [ ] Emails link to Altimeter projects
- [ ] Drafts include project context
- [ ] Tasks extract from emails
- [ ] Calendar syncs from Google Calendar
- [ ] Vector search returns relevant results
- [ ] Document control works (promote, lock)
- [ ] Knowledge base accessible

### Security Audit

- [ ] No secrets in git history
- [ ] CORS configured correctly
- [ ] SQL injection prevented (ORM queries)
- [ ] XSS prevented (HTML sanitization)
- [ ] File uploads validated
- [ ] Authentication required for sensitive endpoints
- [ ] Session management secure

---

## FINAL AUDIT REPORT FORMAT

After completing the audit, generate a report:

```markdown
# ATLAS SYSTEM AUDIT REPORT
**Date**: [YYYY-MM-DD]
**Audited By**: [LLM Name/User]
**Scope**: Full system audit

---

## EXECUTIVE SUMMARY

**Total Issues Found**: [Number]
- Critical: [X] 🔴
- High: [X] 🟠
- Medium: [X] 🟡
- Low: [X] 🟢

**Top 3 Priorities**:
1. [Most critical issue]
2. [Second most critical]
3. [Third most critical]

---

## ERRORS (Critical Issues)
[List all errors found with file:line and fix]

---

## INCOMPLETE IMPLEMENTATIONS
[List all stub functions, missing features]

---

## UX FRICTION POINTS
[List all usability issues with user impact]

---

## PERFORMANCE BOTTLENECKS
[List all slow operations with measurements]

---

## SECURITY VULNERABILITIES
[List all security issues with severity]

---

## INTEGRATION GAPS
[List all broken integrations]

---

## RECOMMENDED PRIORITY ORDER

### Fix Immediately (Blockers):
1. [Issue 1]
2. [Issue 2]

### Fix This Week (High Priority):
1. [Issue 3]
2. [Issue 4]

### Fix Next Sprint (Medium Priority):
1. [Issue 5]
2. [Issue 6]

### Fix Eventually (Low Priority):
1. [Issue 7]
2. [Issue 8]

---

## POSITIVE FINDINGS

What's working well:
- [Feature 1] works correctly
- [Feature 2] has good UX
- [Component 3] is performant

---

**End of Audit Report**
```

---

## HOW TO USE THIS PROMPT

### For a Quick Audit (30 minutes)

```
Run through Backend Audit checklist and Frontend Audit checklist.
Focus on Critical and High severity issues only.
Generate summary report with top 5 fixes.
```

### For a Comprehensive Audit (2-3 hours)

```
Complete all 6 parts systematically:
1. Error Detection
2. Incomplete Implementations
3. UX Friction Analysis
4. Performance Bottlenecks
5. Security Vulnerabilities
6. Integration Gaps

Generate full audit report with all findings prioritized.
```

### For a Targeted Audit (specific area)

```
Audit only [Backend | Frontend | UX | Performance | Security | Integrations]
Focus on [specific component or feature]
Report findings in standard format
```

---

**Start your audit now and identify what needs fixing to make Atlas production-ready!**
