from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
import uuid
import logging
from datetime import datetime
import traceback

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
    yield
    # Shutdown
    scheduler_service.shutdown()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Atlas Personal AI Assistant Backend",
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = str(uuid.uuid4())
    error_msg = str(exc)

    # Log the full traceback with correlation_id
    logging.error(f"Global Exception [CID: {correlation_id}]: {error_msg}")
    logging.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": error_msg,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        }
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
from api.task_routes import router as task_router
from api.calendar_routes import router as calendar_router
from api.search_routes import router as search_router
from api.knowledge_routes import router as knowledge_router
from api.weather_routes import router as weather_router

app.include_router(api_router, prefix=settings.API_PREFIX)

