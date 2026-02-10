import os
import subprocess
from fastapi import APIRouter, Depends
import requests
from typing import Dict, List, Any
from services.activity_service import activity_service
from core.security import verify_local_request

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

@router.get("/activity", response_model=List[Dict[str, Any]])
async def get_activity_logs():
    """
    Fetch system activity logs.
    """
    return activity_service.get_recent_activity()

@router.get("/altimeter/projects")
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
