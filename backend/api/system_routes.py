import os
import subprocess
from fastapi import APIRouter
import requests
from typing import Dict, List, Any
from services.activity_service import activity_service

router = APIRouter()

@router.get("/health", response_model=Dict)
async def system_health():
    """
    Check health of Atlas and connected systems (Altimeter).
    """
    from services.status_service import get_health_status
    return await get_health_status()

@router.post("/control/{action}")
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

@router.get("/geo/status")
async def get_geo_status():
    """
    Check status of geospatial services.
    """
    # Stubbed response for now, can be connected to real service later
    return {
        "status": "offline", 
        "message": "Geospatial Service Unavailable",
        "details": "Map tiles server not responding"
    }
