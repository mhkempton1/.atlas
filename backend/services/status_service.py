from database.database import SessionLocal
from sqlalchemy import text
from typing import Dict, Any

async def get_health_status() -> Dict[str, Any]:
    """
    Unified health check for Atlas and Altimeter.
    """
    from services.scheduler_service import scheduler_service
    from services.altimeter_service import altimeter_service
    
    status = "online"
    details = {}
    
    # 1. Database Check
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        status = "degraded"
    
    # 2. Scheduler Check
    scheduler_health = await scheduler_service.get_system_health()
    
    # 3. Altimeter Check (Direct DB)
    alt_health = altimeter_service.check_health()
    altimeter_core = "disconnected"
    if alt_health["status"] == "connected":
        altimeter_core = "connected"
    else:
        status = "degraded"
        details["altimeter_error"] = alt_health.get("details", "Direct DB connection failed")

    return {
        "status": status,
        "atlas_backend": "operational",
        "altimeter_core": altimeter_core,
        "scheduler": scheduler_health.get("status", "unknown"),
        "database": db_status,
        "details": details
    }
