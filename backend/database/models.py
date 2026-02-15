from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    full_name = Column(String, nullable=True)

class SystemActivity(Base):
    __tablename__ = "system_activity"

    activity_id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True) # e.g., "system", "security", "user"
    action = Column(String)
    target = Column(String)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class TaskQueue(Base):
    __tablename__ = "task_queue"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True) # e.g., "ingest", "analyze", "report"
    payload = Column(JSON)
    status = Column(String, default="pending", index=True) # pending, processing, completed, failed
    priority = Column(Integer, default=0, index=True) # Higher number = higher priority
    agent_id = Column(String, nullable=True) # ID/Name of the agent processing this
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

class Email(Base):
    __tablename__ = "emails"

    email_id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, index=True)
    thread_id = Column(String, index=True, nullable=True)
    remote_id = Column(String, unique=True, index=True) # Unified field for Gmail ID, IMAP UID, etc.
    provider_type = Column(String, default="google", index=True) # e.g., "google", "imap", "internal"
    from_address = Column(String, index=True)
    from_name = Column(String)
    to_addresses = Column(JSON)
    cc_addresses = Column(JSON, nullable=True)
    bcc_addresses = Column(JSON, nullable=True)
    subject = Column(Text)
    body_text = Column(Text)
    body_html = Column(Text)
    snippet = Column(String(200), nullable=True)
    date_received = Column(DateTime(timezone=True))
    date_sent = Column(DateTime(timezone=True), nullable=True)
    labels = Column(JSON, nullable=True)
    category = Column(String, default="inbox", index=True)
    importance = Column(String, nullable=True)
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    project_id = Column(String, index=True, nullable=True)
    contact_id = Column(Integer, nullable=True)
    raw_eml = Column(Text, nullable=True)
    vector_embedding = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    synced_at = Column(DateTime(timezone=True), server_default=func.now())

    # New fields
    gmail_id = Column(String, unique=True, index=True, nullable=True)
    sender = Column(String, index=True, nullable=True)
    recipients = Column(JSON, nullable=True)
    is_unread = Column(Boolean, default=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    attachment_id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.email_id"))
    filename = Column(String)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    file_path = Column(String)
    storage_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    remote_attachment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String, default="open") # open, completed
    priority = Column(String, default="medium")
    category = Column(String, nullable=True)
    project_id = Column(String, index=True, nullable=True)
    email_id = Column(Integer, ForeignKey("emails.email_id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    original_due_date = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    parent_task_id = Column(Integer, nullable=True)
    created_from = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # New fields
    source = Column(String, nullable=True) # atlas_extracted, altimeter_created, user_created
    assigned_to = Column(String, nullable=True)
    related_altimeter_task_id = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    google_calendar_id = Column(String, unique=True, index=True, nullable=True)
    calendar_id = Column(String, nullable=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    location = Column(String, nullable=True)
    attendees = Column(JSON, nullable=True)
    is_all_day = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Text, nullable=True)
    project_id = Column(String, nullable=True)
    related_email_id = Column(Integer, ForeignKey("emails.email_id"), nullable=True)
    is_declined = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Additional fields to maintain compatibility and usefulness
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    synced_at = Column(DateTime(timezone=True), nullable=True)
    organizer = Column(String, nullable=True)
    status = Column(String, default="confirmed")
    provider_type = Column(String, default="google", index=True)

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    title = Column(String, nullable=True)
    altimeter_customer_id = Column(Integer, nullable=True)
    altimeter_vendor_id = Column(Integer, nullable=True)
    relationship_type = Column(String, nullable=True) # enum: customer, vendor, subcontractor, team, personal
    first_contact_date = Column(DateTime(timezone=True), nullable=True)
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    email_count = Column(Integer, default=0)
    is_starred = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DocumentComment(Base):
    __tablename__ = "document_comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    document_path = Column(String, index=True)
    author = Column(String)
    comment_type = Column(String, default="general") # general, issue
    content = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True) # e.g., "task", "system", "calendar", "health"
    title = Column(String)
    message = Column(Text)
    priority = Column(String, default="medium") # low, medium, high, critical
    is_read = Column(Boolean, default=False, index=True)
    link = Column(String, nullable=True) # Optional URL or internal module link
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

class Learning(Base):
    __tablename__ = "learnings"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    insight = Column(Text)
    source = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
