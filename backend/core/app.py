from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
import asyncio

# Initialize database
from database.database import engine, Base
from database import models
Base.metadata.create_all(bind=engine)

from services.scheduler_service import scheduler_service
from contextlib import asynccontextmanager

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
    from services.altimeter_sync_service import altimeter_sync_service
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

@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "status": "online",
        "version": settings.VERSION,
        "ai_enabled": True
    }

@app.get("/health")
async def health_check():
    from services.status_service import get_health_status
    return await get_health_status()

from api.routes import router as api_router

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)
