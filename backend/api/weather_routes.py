from fastapi import APIRouter, Query
from datetime import datetime, timedelta
import httpx
from typing import Optional

router = APIRouter()

# Default location: Nixa, MO
DEFAULT_LAT = 37.0364
DEFAULT_LON = -93.2974
DEFAULT_LOCATION = "Nixa, MO"

from services.weather_service import weather_service

@router.get("/forecast")
async def get_forecast(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude")
):
    """Returns real weather forecast from Open-Meteo API"""
    return await weather_service.get_weather(lat, lon)

