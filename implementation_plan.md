# Implementation Plan - IMAP Completion

## Phase 1: Preparation
- [x] Create reproduction script/test (`tests/test_imap_provider_manual.py`)

## Phase 2: Implementation
- [x] Enhance `SMTPProvider` to support `extra_headers`.
- [x] Implement `IMAPProvider.reply_to_email`.
- [x] Implement `IMAPProvider.forward_email`.
- [x] Implement `IMAPProvider.trash_email`.
- [x] Implement `IMAPProvider.archive_email`.
- [x] Implement `IMAPProvider.mark_unread`.
- [x] Implement `IMAPProvider.move_to_label`.
- [x] Implement `IMAPProvider.get_labels`.

## Phase 3: Verification
- [x] Run tests to verify all methods work as expected (mocked).
