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
