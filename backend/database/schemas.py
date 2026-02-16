from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class TaskBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    category: Optional[str] = "work"
    project_id: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None

class TaskCreate(TaskBase):
    title: str # Required

class TaskUpdate(TaskBase):
    status: Optional[str] = None
    safety_ack: Optional[bool] = False # For high risk tasks
    actual_hours: Optional[float] = None
    completed_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    assigned_to: Optional[str] = None

class Task(TaskBase):
    task_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sync_status: Optional[str] = None

    class Config:
        from_attributes = True
