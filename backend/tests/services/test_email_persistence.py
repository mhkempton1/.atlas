import pytest
from services.email_persistence_service import persist_email_to_database
from database.models import Email, EmailAttachment
from datetime import datetime

def test_persist_new_email(db):
    email_data = {
        "gmail_id": "g123",
        "message_id": "m123",
        "subject": "Test Subject",
        "sender": "test@example.com",
        "recipients": ["recipient@example.com"],
        "body_text": "Hello world",
        "is_unread": True,
        "labels": ["INBOX"]
    }

    result = persist_email_to_database(email_data, db)

    assert result["success"] is True
    assert result["action"] == "created"

    email = db.query(Email).filter(Email.gmail_id == "g123").first()
    assert email is not None
    assert email.subject == "Test Subject"
    assert email.sender == "test@example.com"
    assert email.is_unread is True

def test_deduplication(db):
    # Insert first
    email_data = {
        "gmail_id": "g123",
        "subject": "Original",
        "is_unread": True
    }
    persist_email_to_database(email_data, db)

    # Insert again
    email_data_dup = {
        "gmail_id": "g123",
        "subject": "Duplicate", # Should not overwrite subject
        "is_unread": False # Should update this
    }
    result = persist_email_to_database(email_data_dup, db)

    assert result["success"] is True
    assert result["action"] == "updated"

    # Verify count
    count = db.query(Email).filter(Email.gmail_id == "g123").count()
    assert count == 1

    # Verify updates
    email = db.query(Email).filter(Email.gmail_id == "g123").first()
    assert email.subject == "Original" # Immutable field not updated
    assert email.is_unread is False # Mutable field updated

def test_persist_email_with_attachments(db):
    email_data = {
        "gmail_id": "g_att",
        "subject": "With Attachment",
        "attachments": [
            {
                "filename": "test.txt",
                "mime_type": "text/plain",
                "file_size": 100,
                "storage_path": "/tmp/test.txt"
            }
        ]
    }

    result = persist_email_to_database(email_data, db)
    assert result["success"] is True

    email = db.query(Email).filter(Email.gmail_id == "g_att").first()
    assert email is not None

    attachments = db.query(EmailAttachment).filter(EmailAttachment.email_id == email.email_id).all()
    assert len(attachments) == 1
    assert attachments[0].filename == "test.txt"
    assert attachments[0].storage_path == "/tmp/test.txt"

def test_deduplication_by_message_id(db):
    # Insert with message_id but no gmail_id
    email_data = {
        "message_id": "msg_123",
        "subject": "Message ID Test"
    }
    persist_email_to_database(email_data, db)

    # Insert again with same message_id and new gmail_id
    email_data_update = {
        "message_id": "msg_123",
        "gmail_id": "g_new_123",
        "is_unread": False
    }
    result = persist_email_to_database(email_data_update, db)

    assert result["success"] is True
    assert result["action"] == "updated"

    email = db.query(Email).filter(Email.message_id == "msg_123").first()
    assert email.gmail_id == "g_new_123" # Should be updated
    assert email.is_unread is False
