from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
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
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

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
    gmail_id = Column(String, unique=True, index=True)
    message_id = Column(String, index=True)
    thread_id = Column(String, index=True, nullable=True)
    subject = Column(String)
    from_address = Column(String, index=True)
    from_name = Column(String)
    to_addresses = Column(JSON)
    body_text = Column(Text)
    body_html = Column(Text)
    snippet = Column(String, nullable=True)
    date_received = Column(DateTime(timezone=True))
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False)
    category = Column(String, default="inbox", index=True)
    project_id = Column(String, index=True, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())

class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.email_id"))
    filename = Column(String)
    file_path = Column(String)
    content_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    priority = Column(String, default="medium")
    due_date = Column(DateTime(timezone=True), nullable=True)
    project_id = Column(String, index=True, nullable=True)
    email_id = Column(Integer, ForeignKey("emails.email_id"), nullable=True)
    created_from = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="open") # open, completed

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    event_id = Column(Integer, primary_key=True, index=True)
    google_event_id = Column(String, unique=True, index=True, nullable=True)
    calendar_id = Column(String, nullable=True)
    title = Column(String)
    description = Column(Text)
    location = Column(String)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    all_day = Column(Boolean, default=False)
    status = Column(String, default="confirmed")
    organizer = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    email_id = Column(Integer, ForeignKey("emails.email_id"), nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=True)

class Contact(Base):
    __tablename__ = "contacts"

    contact_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)

class DocumentComment(Base):
    __tablename__ = "document_comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    document_path = Column(String, index=True)
    author = Column(String)
    content = Column(Text)
    comment_type = Column(String, default="general") # general, issue
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
