# Atlas: The Great Decoupling & Nightly Automation

- [x] **Protocol Implementation**
  - [x] Enhance `core/config.py` with IMAP/SMTP settings.
  - [x] Implement robust `IMAPProvider`.
  - [x] Implement robust `SMTPProvider`.
- [x] **Intelligence Bridge 2.0**
  - [x] Refactor `email_routes.py` to use `comm_service`.
  - [x] Update `process_tasks.py` with Altimeter Mission Intel bridge.
- [x] **Internal Persistence**
  - [x] Ensure `calendar_routes.py` uses internal store as primary.
- [x] **UX Restoration & Enhancement**
  - [x] Implement `MissionIntelSnippet` component.
  - [x] Update `EmailList.jsx` with async scan indicators.
  - [x] Enhance `TaskList.jsx` with Mission Intel visualization.
- [x] **Verification**
  - [x] Final backend/frontend synchronization audit.
- [x] **Nightly Automation**
  - [x] Create `.github/workflows/nightly-jules.yml`.
  - [x] Update `AGENTS.md` with Nightly Mission section.
  - [x] Push to GitHub to activate the schedule.
- [x] **Continuous Improvement Automation**
  - [x] Create `JULES_RUNBOOKS.md` (Strategy Document).
  - [x] Define Day/Night Cycle Prompts.
  - [x] Update `AGENTS.md` with manual scheduling workflow.

## Technical Debt: Test Suite Stabilization
- [ ] **Fix Service Mocking**: Refactor `SearchService` and `GoogleService` tests to use `patch` more effectively for complex return structures.
- [ ] **Environment Isolation**: Ensure `AltimeterService` tests correctly reload configurations to prevent leakage between tests.
- [ ] **Integration Tests**: Stabilize API route tests by properly mocking `BackgroundTasks` and external service dependencies.
## 🚀 Next Steps (Post-Decoupling)

- [x] **IMAP Interactivity**
  - [x] Implement `reply_to_email` in `IMAPProvider`.
  - [x] Implement `archive_email` and `trash_email` (move to Trash folder).
  - [x] Implement `mark_unread`.
- [ ] **Autonomous Loop**
  - [ ] Update `execute_mission.py` to allow file modifications (AI coding).
- [x] **Frontend Verification**
  - [x] Verify `EmailView.jsx` actions work with `IMAPProvider`.
  - [x] Refactor `EmailList.jsx` to use cleaner API parameter passing.

## Architecture Refactoring (Midday Architect)
- [x] **Decoupling**: Injected `SMTPProvider` into `IMAPProvider` via `CommunicationService` to remove hardcoded dependency.
- [x] **Code Quality**: Removed redundant header processing in `SMTPProvider`.
- [x] **Provider Decoupling**: Refactored `IMAPProvider` to remove dependencies on `AltimeterService` and `SearchService`, moving intelligence to `process_tasks.py`.
- [x] **Frontend Code Quality**: Refactored `EmailList.jsx` to use helper functions for styling, removing complex inline logic.

## 🔮 Next Steps

### 1. Autonomous Loop Implementation
- [ ] **Tool Execution**: Update `execute_mission.py` to parse and execute tool calls (e.g., `write_file`, `run_command`) from the LLM response.
- [ ] **Context Injection**: Improve context injection to include file contents when requested.

### 2. Test Suite Stabilization
- [ ] **Pytest Setup**: Install and configure `pytest`.
- [ ] **Mocking Strategy**: Fix flaky tests by improving service mocking.
- [ ] **Environment Isolation**: Ensure tests run in an isolated environment.

### 3. Verification
- [ ] **End-to-End Tests**: Create scripts to verify the full flow from email receipt to task creation.
