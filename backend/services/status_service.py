from database.database import SessionLocal
from sqlalchemy import text
from typing import Dict, Any, List
from datetime import datetime
import time

# Track server start time
_server_start_time = time.time()

async def get_health_status() -> Dict[str, Any]:
    """
    Unified health check for Atlas and Altimeter with detailed diagnostics.
    """
    from services.scheduler_service import scheduler_service
    from services.altimeter_service import altimeter_service
    
    subsystems = []
    
    # 1. Atlas Backend (Always operational if this code is running)
    subsystems.append({
        "name": "Atlas Backend",
        "status": "operational",
        "healthy": True,
        "icon": "server",
        "details": "Core API services running"
    })
    
    # 2. Database Check
    db_healthy = True
    db_error = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        subsystems.append({
            "name": "Database",
            "status": "healthy",
            "healthy": True,
            "icon": "database",
            "details": "PostgreSQL connection active"
        })
    except Exception as e:
        db_healthy = False
        db_error = str(e)
        subsystems.append({
            "name": "Database",
            "status": "unhealthy",
            "healthy": False,
            "icon": "database",
            "error": f"Database connection failed: {str(e)}",
            "remediation": {
                "title": "Restore Database Connection",
                "steps": [
                    "Check if PostgreSQL is running",
                    "Verify DATABASE_URL in .env",
                    "Test connection: psql -U <user> -d <database>"
                ]
            }
        })
    
    # 3. Altimeter Check (Direct DB)
    alt_health = altimeter_service.check_health()
    if alt_health["status"] == "connected":
        subsystems.append({
            "name": "Altimeter Core",
            "status": "connected",
            "healthy": True,
            "icon": "activity",
            "details": "Direct database connection established"
        })
    else:
        subsystems.append({
            "name": "Altimeter Core",
            "status": "disconnected",
            "healthy": False,
            "icon": "activity",
            "error": alt_health.get("details", "Direct DB connection failed"),
            "remediation": {
                "title": "Reconnect Altimeter Database",
                "steps": [
                    "Verify Altimeter database is accessible",
                    "Check ALTIMETER_DB_URL in .env",
                    "Ensure network connectivity to Altimeter DB"
                ]
            }
        })
    
    # 4. Scheduler Check (includes external services)
    scheduler_health = await scheduler_service.get_system_health()
    scheduler_status = scheduler_health.get("status", "unknown")
    
    if scheduler_status == "online":
        subsystems.append({
            "name": "Scheduler",
            "status": "operational",
            "healthy": True,
            "icon": "calendar",
            "details": f"Background jobs running. Services: {', '.join([k for k, v in scheduler_health.get('services', {}).items() if v == 'Online'])}"
        })
    else:
        # Identify which service is causing degradation
        services = scheduler_health.get("services", {})
        offline_services = [k for k, v in services.items() if v != "Online"]
        
        error_msg = f"Degraded due to offline services: {', '.join(offline_services)}"
        remediation_steps = []
        
        if "altimeter" in offline_services:
            remediation_steps.extend([
                "Navigate to: C:\\Users\\mhkem\\.altimeter",
                "Run: python main.py",
                "Verify port 4203 is listening"
            ])
        
        if "vector_db" in offline_services:
            remediation_steps.extend([
                "Check ChromaDB initialization",
                "Verify CHROMA_PATH in .env",
                "Restart backend to reinitialize vector store"
            ])
        
        subsystems.append({
            "name": "Scheduler",
            "status": "degraded",
            "healthy": False,
            "icon": "calendar",
            "error": error_msg,
            "last_check": scheduler_health.get("last_check"),
            "remediation": {
                "title": "Restore Scheduler Services",
                "steps": remediation_steps,
                "command": "cd C:\\Users\\mhkem\\.altimeter && python main.py" if "altimeter" in offline_services else None
            }
        })
    
    # Calculate overall health
    healthy_count = sum(1 for s in subsystems if s["healthy"])
    health_percentage = round((healthy_count / len(subsystems)) * 100)
    overall_status = "online" if health_percentage >= 90 else "degraded"
    
    # Push notification for health degradation
    if overall_status == "degraded":
        from services.notification_service import notification_service
        notification_service.push_notification(
            type="health",
            title="System Degradation Alert",
            message=f"System health dropped to {health_percentage}%. Check System Status for details.",
            priority="high",
            link="/system_status"
        )
    
    # Calculate uptime
    uptime_seconds = int(time.time() - _server_start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_formatted = f"{uptime_hours}h {uptime_minutes}m"
    
    return {
        "status": overall_status,
        "health_percentage": health_percentage,
        "subsystems": subsystems,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": uptime_formatted,
        "server_start": datetime.fromtimestamp(_server_start_time).isoformat()
    }
