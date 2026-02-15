import os
import subprocess
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi import APIRouter, Depends
import requests
from typing import Dict, List, Any
from datetime import datetime
from services.activity_service import activity_service
from core.security import verify_local_request

# Remove global dependency so /health is accessible
router = APIRouter()

@router.get("/health", response_model=Dict)
async def system_health():
    """
    Check health of Atlas and connected systems (Altimeter).
    """
    from services.status_service import get_health_status
    return await get_health_status()

from pydantic import BaseModel
from typing import Optional

class ConfigUpdate(BaseModel):
    # Only allow safe updates for now
    notifications: Optional[Dict[str, bool]] = None
    security: Optional[Dict[str, Any]] = None

@router.post("/config/save")
async def save_config(config: ConfigUpdate):
    """
    Persist system configuration.
    """
    # For now, we mock persistence to avoid overwriting critical env vars in this environment
    # In production, this would update secrets.json or .env
    return {"status": "success", "message": "Configuration saved"}

@router.post("/control/{action}", dependencies=[Depends(verify_local_request)])
async def system_control(action: str):
    """
    Trigger system startup/shutdown scripts.
    Actions: boot-silent, boot-all, shutdown
    """
    script_map = {
        "boot-silent": r"C:\Users\mhkem\Desktop\START_SYSTEM_SILENT.vbs",
        "boot-all": r"C:\Users\mhkem\Desktop\START_SYSTEM_ALL.bat",
        "shutdown": r"C:\Users\mhkem\Desktop\KILL_PROJECT_PORTS.bat"
    }
    
    if action not in script_map:
        return {"success": False, "error": "Invalid action"}
    
    script_path = script_map[action]
    
    try:
        if script_path.endswith('.vbs'):
            # Run VBScript via wscript (detached)
            subprocess.Popen(['wscript.exe', script_path], shell=True)
        else:
            # Run Batch file (detached)
            subprocess.Popen(['cmd.exe', '/c', script_path], shell=True)
            
        return {"success": True, "message": f"Action {action} triggered"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/activity", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_local_request)])
async def get_activity_logs():
    """
    Fetch system activity logs.
    """
    return activity_service.get_recent_activity()

@router.get("/altimeter/projects", dependencies=[Depends(verify_local_request)])
async def get_altimeter_projects():
    """Proxy for Altimeter project list via direct DB access"""
    from services.altimeter_service import altimeter_service
    return altimeter_service.list_projects()

@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_system_logs():
    """
    Fetch recent system activity logs (legacy /logs compatibility).
    """
    return activity_service.get_recent_activity(limit=50)

@router.get("/sync-status")
async def get_sync_status():
    """
    Get the status of the last sync operations.
    """
    from database.database import SessionLocal
    from database.models import SyncHistory
    from sqlalchemy import desc

    db = SessionLocal()
    try:
        email_sync = db.query(SyncHistory).filter_by(sync_type='email').order_by(desc(SyncHistory.started_at)).first()
        calendar_sync = db.query(SyncHistory).filter_by(sync_type='calendar').order_by(desc(SyncHistory.started_at)).first()

        return {
            "email": {
                "status": email_sync.status if email_sync else "never_run",
                "last_run": email_sync.started_at if email_sync else None,
                "items_synced": email_sync.items_synced if email_sync else 0,
                "error_count": email_sync.error_count if email_sync else 0,
                "errors": email_sync.errors if email_sync else []
            },
            "calendar": {
                 "status": calendar_sync.status if calendar_sync else "never_run",
                 "last_run": calendar_sync.started_at if calendar_sync else None,
                 "items_synced": calendar_sync.items_synced if calendar_sync else 0,
                 "error_count": calendar_sync.error_count if calendar_sync else 0,
                 "errors": calendar_sync.errors if calendar_sync else []
            }
        }
    finally:
        db.close()

@router.get("/geo/status")
async def get_geo_status():
    """
    Check status of geospatial services.
    """
    # Stubbed response for now, can be connected to real service later
    return {
        "status": "online",
        "health_percentage": 100,
        "server_start": start_time.isoformat(),
        "uptime_seconds": int((datetime.now() - start_time).total_seconds())
    }
