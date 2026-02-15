from sqlalchemy.orm import Session
from database.models import Email, EmailAttachment
from datetime import datetime, timezone
import json

def persist_email_to_database(email_data, db: Session):
    """
    Persist an email object to the database.
    Handles deduplication and updates for existing emails.

    Args:
        email_data: Dictionary or object containing email fields.
        db: SQLAlchemy database session.

    Returns:
        dict: {"success": bool, "email_id": int, "action": str, "error": str}
    """
    # 1. Extract identification fields
    gmail_id = _get_field(email_data, 'gmail_id') or _get_field(email_data, 'id')
    message_id = _get_field(email_data, 'message_id')
    remote_id = _get_field(email_data, 'remote_id') or gmail_id

    # 2. Check existence
    existing_email = None
    if gmail_id:
        existing_email = db.query(Email).filter(Email.gmail_id == gmail_id).first()
    if not existing_email and remote_id:
        existing_email = db.query(Email).filter(Email.remote_id == remote_id).first()
    if not existing_email and message_id:
        existing_email = db.query(Email).filter(Email.message_id == message_id).first()

    # 3. Update or Create
    if existing_email:
        # Update mutable fields
        is_unread = _get_field(email_data, 'is_unread')
        if is_unread is None:
             # Try is_read
             is_read = _get_field(email_data, 'is_read')
             if is_read is not None:
                 is_unread = not is_read

        if is_unread is not None:
            existing_email.is_unread = is_unread
            existing_email.is_read = not is_unread

        is_starred = _get_field(email_data, 'is_starred')
        if is_starred is not None:
            existing_email.is_starred = is_starred

        labels = _get_field(email_data, 'labels')
        if labels is not None:
            existing_email.labels = labels

        # Sync timestamp
        existing_email.synced_at = datetime.now(timezone.utc)

        # Ensure gmail_id is set if it was missing but found by other means and provided now
        if gmail_id and not existing_email.gmail_id:
            existing_email.gmail_id = gmail_id

        try:
            db.commit()
            db.refresh(existing_email)
            return {"success": True, "email_id": existing_email.email_id, "action": "updated"}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    else:
        # Create new
        new_email = Email()

        # Map fields
        new_email.gmail_id = gmail_id
        new_email.remote_id = remote_id
        new_email.message_id = message_id
        new_email.subject = _get_field(email_data, 'subject')

        sender = _get_field(email_data, 'sender') or _get_field(email_data, 'from_address')
        new_email.sender = sender
        new_email.from_address = sender # redundancy handling

        # Recipients
        recipients = _get_field(email_data, 'recipients')
        if not recipients:
             to = _get_field(email_data, 'to_addresses')
             if to: recipients = to
        new_email.recipients = recipients
        new_email.to_addresses = recipients # redundancy handling

        new_email.date_received = _get_field(email_data, 'date_received') or datetime.now(timezone.utc)
        new_email.body_text = _get_field(email_data, 'body_text')
        new_email.body_html = _get_field(email_data, 'body_html')
        new_email.labels = _get_field(email_data, 'labels')

        is_unread = _get_field(email_data, 'is_unread')
        if is_unread is None:
             is_read = _get_field(email_data, 'is_read')
             if is_read is not None:
                 is_unread = not is_read
             else:
                 is_unread = True # Default
        new_email.is_unread = is_unread
        new_email.is_read = not is_unread

        new_email.is_starred = _get_field(email_data, 'is_starred') or False
        new_email.thread_id = _get_field(email_data, 'thread_id')
        new_email.has_attachments = _get_field(email_data, 'has_attachments') or False
        new_email.created_at = datetime.now(timezone.utc)
        new_email.synced_at = datetime.now(timezone.utc)

        try:
            db.add(new_email)
            db.flush() # Get email_id

            # Handle attachments
            attachments = _get_field(email_data, 'attachments') or []
            for att_data in attachments:
                att = EmailAttachment(
                    email_id=new_email.email_id,
                    filename=_get_field(att_data, 'filename'),
                    mime_type=_get_field(att_data, 'mime_type'),
                    file_size=_get_field(att_data, 'file_size'),
                    file_hash=_get_field(att_data, 'file_hash'),
                    storage_path=_get_field(att_data, 'storage_path') or _get_field(att_data, 'file_path'),
                    created_at=datetime.now(timezone.utc)
                )
                db.add(att)

            db.commit()
            db.refresh(new_email)
            return {"success": True, "email_id": new_email.email_id, "action": "created"}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

def _get_field(obj, field_name):
    if isinstance(obj, dict):
        return obj.get(field_name)
    return getattr(obj, field_name, None)
