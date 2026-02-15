from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Task
from services.altimeter_service import altimeter_service
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class TaskStats(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

class ProjectContext(BaseModel):
    project_id: str
    name: str
    status: str
    pm: str
    foreman: str
    percent_complete: Optional[int] = 0
    tasks: TaskStats

@router.get("/{project_id}/context", response_model=ProjectContext)
async def get_project_context(project_id: str, db: Session = Depends(get_db)):
    # 1. Fetch from Altimeter
    details = altimeter_service.get_project_details(project_id)

    if not details:
        # Graceful fallback for missing projects
        details = {
            "altimeter_project_id": project_id,
            "name": "Unknown Project",
            "status": "Unknown",
            "percent_complete": 0
        }

    # 2. Fetch Tasks (Local)
    # Filter by project_id and status (exclude done/completed)
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status.notin_(['done', 'completed'])
    ).all()

    stats = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for task in tasks:
        p = (task.priority or 'medium').lower()
        if p == 'critical' or p == 'urgent':
            stats['critical'] += 1
        elif p == 'high':
            stats['high'] += 1
        elif p == 'medium':
            stats['medium'] += 1
        else:
            stats['low'] += 1

    # 3. Resolve People
    pm_name = "Unassigned"
    foreman_name = "Unassigned"

    # Helper to safe fetch name
    def get_employee_name(emp_id):
        try:
            # Ensure integer ID for safety
            safe_id = int(emp_id)
            rows = altimeter_service.execute_read_only_query(
                f"SELECT first_name, last_name FROM employees WHERE id = {safe_id}"
            )
            if rows and isinstance(rows, list) and len(rows) > 0 and 'first_name' in rows[0]:
                return f"{rows[0]['first_name']} {rows[0]['last_name']}"
        except Exception:
            pass
        return None

    if details.get("project_manager_id"):
        name = get_employee_name(details["project_manager_id"])
        if name:
            pm_name = name

    if details.get("foreman_id"):
        name = get_employee_name(details["foreman_id"])
        if name:
            foreman_name = name

    return ProjectContext(
        project_id=str(details.get("altimeter_project_id", project_id)),
        name=details.get("name", "Unknown Project"),
        status=details.get("status", "Unknown"),
        pm=pm_name,
        foreman=foreman_name,
        percent_complete=details.get("percent_complete", 0),
        tasks=TaskStats(**stats)
    )
