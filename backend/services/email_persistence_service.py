from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, cast, String, desc
from database.models import Email, EmailAttachment
from datetime import datetime, timezone
import json
from services.contact_persistence_service import update_contact_from_email
from services.project_detection_service import project_detection_service
from services.altimeter_service import altimeter_service

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

        # Project Detection
        try:
            full_text = (new_email.subject or "") + "\n" + (new_email.body_text or new_email.body_html or "")
            detected_numbers = project_detection_service.detect_project_number_in_email(full_text)

            if detected_numbers:
                matches = project_detection_service.match_detected_projects_to_altimeter(detected_numbers, altimeter_service)
                if matches:
                    # Set to first match
                    new_email.project_id = matches[0]["number"]

                    if len(matches) > 1:
                        current_labels = new_email.labels or []
                        if isinstance(current_labels, str):
                            # Handle case where labels might be a string (though unlikely for JSON field)
                            try:
                                current_labels = json.loads(current_labels)
                            except:
                                current_labels = [current_labels]

                        if not isinstance(current_labels, list):
                             current_labels = []

                        if "Multiple Projects Detected" not in current_labels:
                            current_labels.append("Multiple Projects Detected")
                        new_email.labels = current_labels
        except Exception as e:
            print(f"Error during project detection for email {new_email.message_id}: {e}")
            # Do not fail email persistence

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

            # Update contacts for new email
            try:
                update_contact_from_email(new_email.sender, db)
                recipients = new_email.recipients or new_email.to_addresses
                if recipients:
                    if isinstance(recipients, list):
                        for recipient in recipients:
                            update_contact_from_email(recipient, db)
                    elif isinstance(recipients, str):
                         update_contact_from_email(recipients, db)
            except Exception as e:
                print(f"Error updating contacts for email {new_email.email_id}: {e}")
                # Don't fail the email persistence if contact update fails

            # Generate Embedding (Sync)
            try:
                from services.embedding_service import embedding_service
                embedding_service.generate_email_embedding({
                    "body": new_email.body_text or new_email.body_html,
                    "subject": new_email.subject,
                    "sender": new_email.from_address,
                    "date": new_email.date_received.isoformat() if new_email.date_received else "",
                    "message_id": new_email.message_id
                })
            except Exception as e:
                print(f"Error generating embedding for email {new_email.email_id}: {e}")

            return {"success": True, "email_id": new_email.email_id, "action": "created"}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

def _get_field(obj, field_name):
    if isinstance(obj, dict):
        return obj.get(field_name)
    return getattr(obj, field_name, None)

def search_emails_local(query, filter_options, db: Session, limit: int = 20, offset: int = 0):
    """
    Search emails locally in the database.

    Args:
        query (str): Search string.
        filter_options (dict): Filters like from_addr, to_addr, date_range, labels.
        db (Session): Database session.
        limit (int): Max results.
        offset (int): Pagination offset.

    Returns:
        list: List of Email objects.
    """
    base_query = db.query(Email)

    # 1. Text Search (Partial match)
    if query:
        search_term = f"%{query}%"
        conditions = []

        subject_only = filter_options.get('subject_only')
        body_only = filter_options.get('body_only')

        if subject_only:
            conditions.append(Email.subject.ilike(search_term))
        elif body_only:
            conditions.append(Email.body_text.ilike(search_term))
        else:
            conditions.append(Email.subject.ilike(search_term))
            conditions.append(Email.body_text.ilike(search_term))

        base_query = base_query.filter(or_(*conditions))

    # 2. Apply Filters
    if filter_options:
        # From Address
        from_addr = filter_options.get('from_addr')
        if from_addr:
            term = f"%{from_addr}%"
            base_query = base_query.filter(
                or_(
                    Email.from_address.ilike(term),
                    Email.sender.ilike(term)
                )
            )

        # To Address (JSON field)
        to_addr = filter_options.get('to_addr')
        if to_addr:
            # Cast JSON to string for simple partial match
            term = f"%{to_addr}%"
            base_query = base_query.filter(
                or_(
                    cast(Email.to_addresses, String).ilike(term),
                    cast(Email.recipients, String).ilike(term)
                )
            )

        # Labels (JSON field)
        label = filter_options.get('labels')
        if label:
            term = f"%{label}%"
            base_query = base_query.filter(cast(Email.labels, String).ilike(term))

        # Date Range
        date_range = filter_options.get('date_range')
        if date_range:
            start = date_range.get('start')
            end = date_range.get('end')
            if start:
                base_query = base_query.filter(Email.date_received >= start)
            if end:
                base_query = base_query.filter(Email.date_received <= end)

    # 3. Sorting (Date Descending)
    base_query = base_query.order_by(desc(Email.date_received))

    # 4. Pagination
    if limit:
        base_query = base_query.limit(limit)
    if offset:
        base_query = base_query.offset(offset)

    return base_query.all()
