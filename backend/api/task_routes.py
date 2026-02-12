from fastapi import APIRouter, Depends, HTTPException
from database.database import get_db
from database.models import Task
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from services.activity_service import activity_service

router = APIRouter()

class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    category: Optional[str] = "work"
    project_id: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None

class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    project_id: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    # Foreman Protocol: Safety Acknowledgement
    safety_ack: Optional[bool] = False

@router.get("/list")
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get tasks with optional filtering.

    Args:
        status: Filter by task status.
        priority: Filter by task priority.
        category: Filter by task category.
        db: Database session.

    Returns:
        A list of tasks matching the criteria.
    """
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if category:
        query = query.filter(Task.category == category)

    # Active tasks first, then by priority, then by due date
    try:
        # Sort by status (asc), then due_date (nulls last)
        # In SQLite/SQLAlchemy, we can use nullslast() if the engine supports it, 
        # but a common robust way is using a case statement or just simple asc()
        tasks = query.order_by(
            Task.status.asc(),
            Task.due_date.asc()
        ).all()
    except Exception:
        tasks = query.all()

    return [
        {
            "task_id": t.task_id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "category": t.category,
            "project_id": t.project_id,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "estimated_hours": t.estimated_hours,
            "actual_hours": t.actual_hours,
            "created_from": t.created_from,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        }
        for t in tasks
    ]

@router.post("/create")
async def create_task(request: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task.

    Args:
        request: The task creation data.
        db: Database session.

    Returns:
        The created task summary.
    """
    task = Task(
        title=request.title,
        description=request.description,
        status=request.status,
        priority=request.priority,
        category=request.category,
        project_id=request.project_id,
        due_date=request.due_date,
        original_due_date=request.due_date,
        estimated_hours=request.estimated_hours,
        created_from="manual",
        created_at=datetime.now()
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    activity_service.log_activity(
        type="task",
        action="Task Created",
        target=task.title,
        details=f"Priority: {task.priority}, Status: {task.status}"
    )

    return {"task_id": task.task_id, "title": task.title, "status": task.status}

@router.put("/{task_id}")
async def update_task(task_id: int, request: TaskUpdate, db: Session = Depends(get_db)):
    """
    Update an existing task.

    Args:
        task_id: The ID of the task to update.
        request: The update data.
        db: Database session.

    Returns:
        The updated task summary.
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status

    # Foreman Protocol: The Gatekeeper
    # If High Priority and moving to In Progress, enforce safety acknowledgement
    if (task.priority == "high" or "high-risk" in (task.description or "").lower()) \
       and request.status == "in_progress" and old_status != "in_progress":
        if not request.safety_ack:
             raise HTTPException(
                status_code=403,
                detail="Safety Acknowledgement Required: High-risk tasks cannot proceed without explicit safety confirmation."
            )

    # Apply updates (only non-None fields)
    for field, value in request.model_dump(exclude_none=True).items():
        if field == "safety_ack": continue # Don't try to set on DB model
        setattr(task, field, value)

    # Auto-set completed_at when status changes to done
    if request.status == "done" and old_status != "done":
        task.completed_at = datetime.now()
    elif request.status and request.status != "done":
        task.completed_at = None

    db.commit()
    db.refresh(task)

    activity_service.log_activity(
        type="task",
        action="Task Updated",
        target=task.title,
        details=f"Status: {old_status} → {task.status}" if request.status else "Fields updated"
    )

    return {"task_id": task.task_id, "title": task.title, "status": task.status}

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a task.

    Args:
        task_id: The ID of the task to delete.
        db: Database session.

    Returns:
        Success message.
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    db.delete(task)
    db.commit()

    activity_service.log_activity(
        type="task",
        action="Task Deleted",
        target=title
    )

    return {"success": True, "message": f"Task '{title}' deleted"}

@router.post("/extract/{email_id}")
async def extract_tasks(email_id: int, db: Session = Depends(get_db)):
    """
    Manually trigger AI task extraction for a specific email.

    Args:
        email_id: The ID of the email to process.
        db: Database session.

    Returns:
        Result of the extraction process.
    """
    from database.models import Email
    from agents.task_agent import task_agent
    from services.altimeter_service import altimeter_service

    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    context = altimeter_service.get_context_for_email(email.from_address, email.subject)
    agent_context = {
        "subject": email.subject,
        "sender": email.from_address,
        "body": email.body_text or "",
        "message_id": email.message_id
    }

    result = await task_agent.process(agent_context)
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("error"))

    tasks_created = []
    for t_data in result["data"].get("tasks", []):
        task = Task(
            title=t_data["title"],
            description=t_data["description"],
            priority=t_data["priority"].lower(),
            due_date=datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
            original_due_date=datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
            project_id=context.get("project", {}).get("number") if context.get("project") else None,
            email_id=email_id,
            created_from="email"
        )
        db.add(task)
        db.flush()
        tasks_created.append({"task_id": task.task_id, "title": task.title})

    db.commit()
    return {"extracted": len(tasks_created), "tasks": tasks_created}
