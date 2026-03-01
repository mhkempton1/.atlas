from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
import asyncio
import logging

# Initialize database
from database.database import engine, Base
from database import models
Base.metadata.create_all(bind=engine)

from services.scheduler_service import scheduler_service
from contextlib import asynccontextmanager
from services.websocket_manager import ws_manager
from services.altimeter_sync_service import altimeter_sync_service

# Set WebSocket manager in sync service
altimeter_sync_service.set_ws_manager(ws_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from services.activity_service import activity_service
    activity_service.log_activity(
        type="system",
        action="Core Services Online",
        target="Atlas Backend",
        details="System successfully initialized and recovered from previous fault."
    )
    scheduler_service.start()

    # Start Sync Worker
    sync_worker_task = asyncio.create_task(altimeter_sync_service.start_worker())

    yield
    # Shutdown
    scheduler_service.shutdown()
    altimeter_sync_service.stop_worker()
    # Wait for sync worker to finish (optional but good practice)
    # await sync_worker_task

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Atlas Personal AI Assistant Backend",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/sync-status")
async def websocket_sync_status(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sync status updates.
    Frontend connects here to receive sync events.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages (if any)
            data = await websocket.receive_text()
            # We don't expect clients to send data, but this keeps connection open
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logging.getLogger("app").error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.routes import router as api_router

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)

# Serve Frontend UI
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.exists(frontend_dist):
    # Mount assets folder for JS/CSS
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
    # Optional: other public folders commonly found in React builds
    for folder in ["icons", "fonts", "images"]:
        folder_path = os.path.join(frontend_dist, folder)
        if os.path.exists(folder_path):
             app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)
    
    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
            
        # Serve exact files if they exist in dist root (like favicon.ico, manifest.json)
        full_file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(full_file_path):
            return FileResponse(full_file_path)
            
        # Fallback to index.html for Single Page Application routing
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend UI not found"}
else:
    @app.get("/")
    async def root():
        return {
            "system": settings.APP_NAME,
            "status": "online but frontend not compiled",
            "version": settings.VERSION,
            "ai_enabled": True
        }

@app.get("/health")
async def health_check():
    from services.status_service import get_health_status
    return await get_health_status()
