from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from core.config import settings

scheduler = BackgroundScheduler()

def sync_emails_job():
    """Background job to sync emails with retry and persistence."""
    from services.communication_service import comm_service
    from services.notification_service import notification_service
    from database.database import SessionLocal
    from database.models import Email, SyncHistory
    import time

    db = SessionLocal()
    
    # Create Sync History
    history = SyncHistory(
        sync_type='email',
        status='started',
        started_at=datetime.now()
    )
    try:
        db.add(history)
        db.commit()
        db.refresh(history)

        # Get last sync
        last_email = db.query(Email).order_by(Email.date_received.desc()).first()
        last_sync = last_email.date_received if last_email else None

        # Sync with Retry
        retries = 5
        result = None
        last_error = None

        for attempt in range(retries):
            try:
                result = comm_service.sync_emails(last_sync)
                if result.get('status') == 'error':
                     raise Exception(result.get('errors', ['Unknown error'])[0])
                break
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e

        # Update History on Success/Partial
        history.status = result.get('status', 'success')
        history.items_synced = result.get('synced', 0)
        history.errors = result.get('errors', [])
        history.error_count = len(result.get('errors', []))
        history.completed_at = datetime.now()
        db.commit()

    except Exception as e:
        # Update History on Failure
        if history:
            history.status = 'failed'
            history.errors = [str(e)]
            history.error_count = 1
            history.completed_at = datetime.now()
            db.commit()
            
        notification_service.push_notification(
            type="system",
            title="Email Sync Failed",
            message=f"Sync failed: {str(e)}",
            priority="high"
        )
    finally:
        db.close()

def sync_calendar_job():
    """Background job to sync calendar every 15 minutes."""
    from services.communication_service import comm_service
    from services.notification_service import notification_service
    from services.calendar_persistence_service import calendar_persistence_service
    from database.database import SessionLocal
    from datetime import timezone
    
    try:
        result = comm_service.sync_calendar()
        if result and result.get("synced_count", 0) > 0:
            notification_service.push_notification(
                type="calendar",
                title="Calendar Sync Complete",
                message=f"Synced {result['synced_count']} new events from Google Calendar.",
                priority="low"
            )

        # Conflict Detection (Today + 7 days)
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            end_check = now + timedelta(days=7)

            conflicts = calendar_persistence_service.get_conflicts(now, end_check, db)

            if conflicts:
                # Notify about the first one or a summary
                first_conflict = conflicts[0]
                e1 = first_conflict['event_1']
                e2 = first_conflict['event_2']
                # Determine display time (use local time if possible, or UTC)
                # Since we don't have user timezone, we stick to what we have or just time.
                overlap_time = first_conflict['overlap_start'].strftime("%H:%M")

                msg = f"Double-booked at {overlap_time}: {e1.title} and {e2.title}"
                if len(conflicts) > 1:
                    msg += f" (+{len(conflicts)-1} other conflicts)"

                notification_service.push_notification(
                    type="calendar",
                    title="Schedule Conflict Detected",
                    message=msg,
                    priority="high"
                )
        finally:
            db.close()

    except Exception:
        pass

def sync_tasks_job():
    """Background job to sync tasks from Altimeter for active projects."""
    from services.task_sync_service import task_sync_service
    from database.database import SessionLocal
    from database.models import Task
    from sqlalchemy import distinct

    db = SessionLocal()
    try:
        # Get projects that have linked tasks
        # We only sync projects that are already linked.
        # Query distinct project_id from tasks where related_altimeter_task_id is not null
        project_ids = db.query(distinct(Task.project_id)).filter(Task.related_altimeter_task_id != None).all()

        # project_ids is a list of tuples like [('P-123',), ('P-456',)]

        for p_row in project_ids:
            project_id = p_row[0]
            if project_id:
                 try:
                     task_sync_service.sync_tasks_from_altimeter(project_id, db)
                 except Exception as e:
                     # Log error per project but continue
                     pass

    except Exception as e:
        pass
    finally:
        db.close()

def watchtower_job():
    """
    The Watchtower: Proactive Risk Scanning.
    Checks Weather + Active Phases for risks.
    """
    from services.altimeter_service import altimeter_service, intelligence_bridge
    from services.weather_service import weather_service
    from services.activity_service import activity_service

    try:
        # 1. Get Forecast
        # get_weather is async, but watchtower_job is run in a background thread.
        weather = asyncio.run(weather_service.get_weather())

        # 2. Get Active Phases
        phases = altimeter_service.get_active_phases()

        # 3. Predict Risks
        intel = intelligence_bridge.predict_mission_intel(phases, weather)

        # 4. Check for 'Weather Alert' triggers
        alerts = [i for i in intel if i.get('trigger') == 'Weather Alert']

        if alerts:
            for alert in alerts:
                msg = f"WATCHTOWER ALERT: {alert['title']} recommended for {alert['phase_match']} due to weather."
                # Log to Activity Feed (User Notification Stub)
                activity_service.log_activity("system", "Risk Detected", msg)

    except Exception:
        pass

# Schedule jobs
scheduler.add_job(sync_emails_job, 'interval', minutes=5, id='email_sync', replace_existing=True)
scheduler.add_job(sync_calendar_job, 'interval', minutes=15, id='calendar_sync', replace_existing=True)
scheduler.add_job(sync_tasks_job, 'interval', minutes=15, id='task_sync', replace_existing=True)
scheduler.add_job(watchtower_job, 'interval', minutes=60, id='watchtower', replace_existing=True)

class SchedulerService:
    """
    Service for managing background jobs and system health checks.
    """
    def __init__(self):
        """Initialize the SchedulerService."""
        pass # Scheduler is global for now, this class wraps other scheduling logic like Altimeter

    def start(self):
        """Start the background scheduler."""
        if not scheduler.running:
            scheduler.start()
            
    def shutdown(self):
        """Shutdown the background scheduler."""
        if scheduler.running:
            scheduler.shutdown()

    def get_my_schedule(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Aggregates data from CalendarEvents and Tasks into a unified format.

        Args:
            employee_id: The ID of the employee to fetch the schedule for.

        Returns:
            A list of schedule items (calendar events and tasks).
        """
        from database.database import SessionLocal
        from database.models import CalendarEvent, Task

        db = SessionLocal()
        combined_schedule = []

        try:
            # 1. Fetch Calendar Events (Next 7 days, including all of today)
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_out = today_start + timedelta(days=7)
            
            events = db.query(CalendarEvent).filter(
                CalendarEvent.start_time >= today_start,
                CalendarEvent.start_time <= week_out
            ).all()

            for event in events:
                combined_schedule.append({
                    "id": f"cal_{event.event_id}",
                    "type": "calendar",
                    "name": event.title,
                    "project_id": event.project_id or "General",
                    "current_start": event.start_time.strftime("%Y-%m-%d %H:%M"),
                    "status": "Confirmed" if event.status == "confirmed" else "Tentative",
                    "description": event.description
                })

            # 2. Fetch Tasks (Pending or In Progress)
            tasks = db.query(Task).filter(
                Task.status.in_(['todo', 'in_progress', 'Prioritized'])
            ).all()

            for task in tasks:
                deviation_days = 0
                if task.due_date and task.original_due_date:
                    deviation_days = (task.due_date - task.original_due_date).days

                combined_schedule.append({
                    "id": f"task_{task.task_id}",
                    "type": "task",
                    "name": task.title,
                    "project_id": task.project_id or "Personal",
                    "current_start": task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No Deadline",
                    "created_at": task.created_at.strftime("%Y-%m-%d"),
                    "original_due_date": task.original_due_date.strftime("%Y-%m-%d") if task.original_due_date else "N/A",
                    "deviation": deviation_days,
                    "status": "Prioritized" if task.priority == "high" else "In Progress" if task.status == "in_progress" else "Pending",
                    "engineering_status": "Approved" if task.status == "done" else "Pending Review"
                })

            # 3. Fetch Altimeter Milestones
            from services.altimeter_service import altimeter_service
            milestones = altimeter_service.get_upcoming_milestones(7)
            for m in milestones:
                combined_schedule.append({
                    "id": f"alt_{m.get('id')}",
                    "type": "altimeter",
                    "name": m.get("title") or m.get("description"),
                    "project_id": m.get("altimeter_project_id"),
                    "current_start": m.get("due_date"),
                    "status": "Milestone",
                    "description": f"Altimeter Project: {m.get('project_name')}"
                })

        finally:
            db.close()

        # 4. Sort and Normalize
        # Use a helper to parse date strings for sorting
        def parse_for_sort(item):
            ds = item.get("current_start")
            if not ds or ds == "No Deadline":
                return datetime.max
            try:
                # Handle YYYY-MM-DD HH:MM
                if " " in ds:
                    return datetime.strptime(ds, "%Y-%m-%d %H:%M")
                # Handle YYYY-MM-DD
                return datetime.strptime(ds, "%Y-%m-%d")
            except:
                return datetime.max

        combined_schedule.sort(key=parse_for_sort)
        
        # Limit to reasonable display size
        return combined_schedule[:50]

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Fetch real-time statistics for the dashboard.
        Offloads blocking DB calls to a thread to prevent blocking the async event loop.

        Returns:
            A dictionary of dashboard statistics.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_dashboard_stats_sync)

    def _get_dashboard_stats_sync(self) -> Dict[str, Any]:
        """
        Synchronous implementation of dashboard stats fetching.
        """
        from database.database import SessionLocal
        from database.models import Task, Email, CalendarEvent
        from services.document_control_service import document_control_service
        from services.altimeter_service import altimeter_service
        
        db = SessionLocal()
        try:
            # 1. Document Stats
            docs = document_control_service.get_all_documents()
            
            # 2. Altimeter Stats
            active_projects = altimeter_service.list_projects()
            active_projects_count = len(active_projects)
            
            # 3. Task & Event Stats
            total_pending_tasks = db.query(Task).filter(Task.status != 'done').count()
            high_priority_tasks = db.query(Task).filter(Task.status != 'done', Task.priority == 'high').count()
            # Today's events should include everything today, even if already started
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            upcoming_events = db.query(CalendarEvent).filter(CalendarEvent.start_time >= today_start).count()
            
            # 3. Email Stats
            total_emails = db.query(Email).count()
            unread_emails = db.query(Email).filter(Email.is_read == False).count()
            
            return {
                "drafts": len(docs.get("draft", [])),
                "reviews": len(docs.get("review", [])),
                "pending_tasks": total_pending_tasks,
                "high_priority_tasks": high_priority_tasks,
                "upcoming_events": upcoming_events,
                "inbox_total": total_emails,
                "inbox_unread": unread_emails,
                "active_projects": active_projects_count,
                "health_score": 98 if total_pending_tasks < 10 else 85
            }
        finally:
            db.close()

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Check status of critical external services.

        Returns:
            A dictionary containing the health status of various components.
        """
        from services.search_service import search_service
        
        # 1. Altimeter Check (via API)
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{settings.ALTIMETER_API_URL}/api/system/health", timeout=1.0)
                altimeter_status = "Online" if res.status_code == 200 else "Degraded"
        except Exception:
            altimeter_status = "Offline"

        # 2. Vector DB Check (via SearchService Internal State)
        vector_db = "Online" if search_service._ensure_initialized() else "Offline"

        # 3. Gmail Check (Stubbed for now)
        gmail_status = "Online"

        return {
            "status": "online" if altimeter_status == "Online" and vector_db == "Online" else "degraded",
            "scheduler": "running" if scheduler.running else "stopped",
            "services": {
                "backend": "Online",
                "gmail": gmail_status,
                "altimeter": altimeter_status,
                "vector_db": vector_db
            },
            "last_check": datetime.now().isoformat()
        }

# Create global instance
scheduler_service = SchedulerService()
