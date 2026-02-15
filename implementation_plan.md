# Implementation Plan - IMAP Features Completion

## Goal Description

Complete the implementation of the `IMAPProvider` in `backend/services/imap_provider.py` to support full email functionality including Reply, Forward, Move, Trash, Archive, Mark Unread, and Get Labels. This ensures that Atlas works with standard IMAP/SMTP providers, not just Google.

## User Review Required
>
> [!IMPORTANT]
> - `CommunicationProvider.send_email` signature has changed to accept `extra_headers`.
> - `IMAPProvider` now requires a configured `SMTPProvider` to send emails (replies/forwards).

## Proposed Changes

### Backend

#### [MODIFY] `backend/services/communication_provider.py`

- Updated `send_email` signature to include `extra_headers`.

#### [MODIFY] `backend/services/smtp_provider.py`

- Updated `send_email` to handle `extra_headers` and inject them into the MIME message (e.g., `In-Reply-To`, `References`).

#### [MODIFY] `backend/services/google_service.py` & `backend/services/gmail_provider.py`

- Updated `send_email` to match the new interface and support `extra_headers`.

#### [MODIFY] `backend/services/imap_provider.py`

- Implemented `reply_to_email`: Fetches original email via IMAP, constructs reply with proper threading headers, and sends via SMTP.
- Implemented `forward_email`: Fetches original email via IMAP, constructs forward body, and sends via SMTP.
- Implemented `move_to_label`: Uses IMAP `COPY` + `STORE \Deleted` + `EXPUNGE`.
- Implemented `trash_email`: Moves to "Trash".
- Implemented `archive_email`: Moves to "Archive".
- Implemented `mark_unread`: Removes `\Seen` flag.
- Implemented `get_labels`: Lists and parses IMAP folders.
- Added helpers: `_get_original_email`, `_extract_body_from_msg`.

### Frontend

No changes.

## Verification Plan

### Automated Tests

- [x] Run `python tests/test_imap_features.py` (New test file created)
- [x] Run `python tests/test_email_providers.py` (Regression check)

### Manual Verification

- [ ] Verify sending emails with headers works if connected to real SMTP.

## Implemented

- [x] Verified `IMAPProvider` implementation via `tests/test_imap_features.py` and `tests/test_email_providers.py`.
- [x] Fixed regression in `tests/test_email_providers.py` regarding `trash_email` case sensitivity and `reply_to_email` configuration.

# Implementation Plan - Test Suite Stabilization

## Goal Description
Fix critical environment configuration issues and refactor service tests (`SearchService`, `GoogleService`) to use correct database models, enabling the test suite to run reliably in CI/CD environments.

## Proposed Changes

### Configuration
#### [MODIFY] `backend/core/config.py`
- Updated `DATABASE_URL`, `ALTIMETER_PATH`, `OBSIDIAN_KNOWLEDGE_PATH`, and `ONEDRIVE_PATH` to use relative path defaults and `os.getenv` overrides, replacing hardcoded absolute Windows paths.

#### [MODIFY] `backend/tests/conftest.py`
- Added explicit `os.environ["DATABASE_URL"] = "sqlite:///./test_atlas.db"` setup to force tests to use a temporary database instead of the production one.

### Tests
#### [MODIFY] `backend/tests/services/test_google_service.py`
- Refactored tests to use `remote_id` instead of `gmail_id` and `remote_event_id` instead of `google_event_id`, aligning with the updated database schema.

### API Route Tests Stabilization
#### [MODIFY] `backend/tests/api/test_scan_route.py`
- Updated `sample_email` fixture to use `remote_id` instead of `gmail_id`.
- Patched `database.database.SessionLocal` to ensure background tasks use the test database session.

#### [MODIFY] `backend/tests/api/test_email_routes.py`
- Updated `sample_email` fixture to use `remote_id` instead of `gmail_id`.
- Patched `services.communication_service.comm_service` instead of `services.google_service.google_service` to align with the decoupled architecture.

#### [MODIFY] `backend/tests/api/test_calendar_routes.py`
- Updated tests to use `remote_event_id` instead of `google_event_id`.

#### [MODIFY] `backend/tests/conftest.py`
- Removed invalid patching of `api.routes.google_service` as the router now correctly uses `comm_service`.

#### [MODIFY] `backend/api/system_routes.py`
- Removed redundant redefinition of `verify_local_request` which was shadowing the secure version from `core.security` (and blocking tests).

## Implemented
- [x] Configuration updated for cross-platform compatibility.
- [x] Test environment isolated from production database.
- [x] `test_google_service.py` and `test_search_service.py` passing.
- [x] All API route tests (`test_scan_route`, `test_email_routes`, `test_calendar_routes`, `test_routes`, `test_system_routes`) are passing.

# Implementation Plan - Notification & Scheduler Tests

## Goal Description
Implement comprehensive test coverage for Notification API routes and Scheduler Service (schedule aggregation, dashboard stats) to ensure reliability and catch regressions.
# Implementation Plan - Notification System Testing

## Goal Description
Implement comprehensive tests for the Notification system, covering both the `NotificationService` and the API routes (`/notifications/*`).

## Proposed Changes

### Tests
#### [CREATE] `backend/tests/api/test_notification_routes.py`
- Implemented tests for `/api/v1/notifications/list` (GET), `/api/v1/notifications/{id}/read` (PATCH), and `/api/v1/notifications/clear` (DELETE).
- Patched `services.notification_service.SessionLocal` to ensure tests run against the isolated test database.

#### [CREATE] `backend/tests/services/test_scheduler_service.py`
- Implemented `test_get_my_schedule` to verify aggregation of Calendar Events, Tasks, and Altimeter Milestones.
- Implemented `test_get_dashboard_stats` to verify system health metrics.
- Patched `database.database.SessionLocal` to intercept internal service DB calls.
- Mocked `services.altimeter_service.altimeter_service` and `services.document_control_service.document_control_service` to isolate the scheduler logic.

## Verification Plan

### Automated Tests
- [x] Run `python -m pytest backend/tests/api/test_notification_routes.py`
- [x] Run `python -m pytest backend/tests/services/test_scheduler_service.py`

## Implemented
- [x] Notification API tests passing.
- [x] Scheduler Service tests passing.

#### [CREATE] `backend/tests/services/test_notification_service.py`
- Implemented unit tests for `NotificationService`:
    - `push_notification`: Verifies creation and persistence.
    - `get_unread_notifications`: Verifies filtering and ordering.
    - `mark_as_read`: Verifies status update.
    - `clear_all`: Verifies deletion.

#### [CREATE] `backend/tests/api/test_notification_routes.py`
- Implemented API tests for `/notifications` endpoints:
    - `GET /list`: Verifies retrieval and `unread_only` filtering.
    - `PATCH /{id}/read`: Verifies marking as read.
    - `DELETE /clear`: Verifies clearing all notifications.
- Added `patch_session` fixture to resolve SQLite locking issues by sharing the connection between test fixture and service.

## Implemented
- [x] `backend/tests/services/test_notification_service.py` passing.
- [x] `backend/tests/api/test_notification_routes.py` passing.
