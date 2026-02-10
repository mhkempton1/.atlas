from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import httpx
import asyncio
from typing import List, Dict, Any, Optional

scheduler = BackgroundScheduler()

def sync_emails_job():
    """Background job to sync emails every 5 minutes"""
    from services.communication_service import comm_service
    from database.database import get_db
    from database.models import Email
    
    # We need to handle DB session internally if not using dependency
    try:
        db = next(get_db())

        # Get last sync
        last_email = db.query(Email).order_by(Email.synced_at.desc()).first()
        last_sync = last_email.synced_at if last_email else None

        # Sync
        try:
            result = comm_service.sync_emails(last_sync)
            print(f"[{datetime.now()}] Email sync: {result['synced']} new emails")
            
            # FUTURE: Extract tasks from new emails here
            # extract_tasks_from_new_emails(db)

        except Exception as e:
            print(f"Email sync failed: {e}")
            
    except Exception as e:
        print(f"Job execution failed: {e}")

def sync_calendar_job():
    """Background job to sync calendar every 15 minutes"""
    from services.communication_service import comm_service
    
    try:
        result = comm_service.sync_calendar()
        print(f"[{datetime.now()}] Calendar sync: {result['synced']} events updated")
    except Exception as e:
        print(f"Calendar sync failed: {e}")

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
                print(f"[Watchtower] {msg}")
                # Log to Activity Feed (User Notification Stub)
                activity_service.log_activity("system", "Risk Detected", msg)

    except Exception as e:
        print(f"Watchtower scan failed: {e}")

# Schedule jobs
scheduler.add_job(sync_emails_job, 'interval', minutes=5, id='email_sync', replace_existing=True)
scheduler.add_job(sync_calendar_job, 'interval', minutes=15, id='calendar_sync', replace_existing=True)
scheduler.add_job(watchtower_job, 'interval', minutes=60, id='watchtower', replace_existing=True)

class SchedulerService:
    def __init__(self):
        pass # Scheduler is global for now, this class wraps other scheduling logic like Altimeter

    def start(self):
        if not scheduler.running:
            scheduler.start()
            
    def shutdown(self):
        if scheduler.running:
            scheduler.shutdown()

    # Reuse existing Altimeter proxy methods for continuity if needed by other components
    # Although prompt replaced the whole file content for "scheduler_service.py" in Step 3?
    # Actually prompt Step 3 says "ENHANCE EXISTING". 
    # The existing file had get_my_schedule and get_system_health.
    # I should preserve them.

    def get_my_schedule(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Aggregates data from CalendarEvents and Tasks into a unified format.
        """
        from database.database import SessionLocal
        from database.models import CalendarEvent, Task
        from datetime import datetime, timedelta

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
        
        db = SessionLocal()
        from services.altimeter_service import altimeter_service
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
        """Check status of critical external services"""
        from services.search_service import search_service
        
        # 1. Altimeter Check (via API)
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get("http://127.0.0.1:4203/api/system/health", timeout=1)
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
