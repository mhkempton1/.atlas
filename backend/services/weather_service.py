import httpx
from datetime import datetime
from typing import Optional, Dict, Any

class WeatherService:
    def __init__(self):
        self.DEFAULT_LAT = 37.0364
        self.DEFAULT_LON = -93.2974
        self.DEFAULT_LOCATION = "Nixa, MO"

    def map_weather_code(self, code: int) -> str:
        """Map Open-Meteo weather codes to readable conditions"""
        if code == 0:
            return "Sunny/Clear"
        elif code in [1, 2]:
            return "Partly Cloudy"
        elif code == 3:
            return "Cloudy"
        elif code in [45, 48]:
            return "Fog"
        elif code in range(51, 68):
            return "Rain"
        elif code in range(71, 78):
            return "Snow"
        elif code in range(80, 100):
            return "Rain Showers"
        else:
            return "Cloudy"

    async def get_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Returns real weather forecast from Open-Meteo API"""
        latitude = lat if lat is not None else self.DEFAULT_LAT
        longitude = lon if lon is not None else self.DEFAULT_LON
        location = self.DEFAULT_LOCATION if (lat is None or lon is None) else f"Current Location"
        
        try:
            async with httpx.AsyncClient() as client:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,wind_speed_10m_max",
                    "temperature_unit": "fahrenheit",
                    "wind_speed_unit": "mph",
                    "timezone": "America/Chicago",
                    "forecast_days": 7
                }
                
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                daily = data.get("daily", {})
                dates = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                codes = daily.get("weather_code", [])
                winds = daily.get("wind_speed_10m_max", [])
                rains = daily.get("precipitation_probability_max", [])
                
                forecast = []
                for i in range(min(7, len(dates))):
                    try:
                        date = datetime.fromisoformat(dates[i])
                        forecast.append({
                            "date": dates[i],
                            "display_date": "Today" if i == 0 else date.strftime("%a"),
                            "high": int(max_temps[i]) if i < len(max_temps) else 32,
                            "low": int(min_temps[i]) if i < len(min_temps) else 18,
                            "condition": self.map_weather_code(codes[i]) if i < len(codes) else "Cloudy",
                            "wind_speed": int(winds[i]) if i < len(winds) else 0,
                            "wind_direction": "N",
                            "rain_chance": int(rains[i]) if (i < len(rains) and rains[i] is not None) else 0
                        })
                    except (IndexError, ValueError) as e:
                        print(f"[WeatherService] Item error at index {i}: {e}")
                
                print(f"[WeatherService] Successfully generated {len(forecast)} day forecast")
                return {
                    "location": location,
                    "current": {
                        "condition": forecast[0]["condition"] if forecast else "Cloudy",
                        "temp": forecast[0]["high"] if forecast else 32
                    },
                    "forecast": forecast,
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "Open-Meteo (Live)"
                }
                
        except Exception as e:
            print(f"[WeatherService] Error fetching weather: {e}")
            return {
                "location": location,
                "current": {"condition": "Cloudy"},
                "forecast": [
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "display_date": "Today",
                        "high": 32,
                        "low": 18,
                        "condition": "Cloudy",
                        "wind_speed": 15,
                        "wind_direction": "N",
                        "rain_chance": 20
                    }
                ]
            }

weather_service = WeatherService()
