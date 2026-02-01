import httpx
import asyncio

async def test_weather():
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": 37.0364,
                "longitude": -93.2974,
                "daily": "temperature_2m_max",
                "temperature_unit": "fahrenheit",
                "forecast_days": 1
            }
            print(f"Requesting {url}...")
            response = await client.get(url, params=params, timeout=10.0)
            print(f"Status: {response.status_code}")
            print(f"Data: {response.json()}")
    except Exception as e:
        print(f"Weather API Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_weather())
