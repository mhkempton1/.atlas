import asyncio
import json
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath('.'))

from services.weather_service import weather_service

async def test_weather():
    print("Fetching weather...")
    try:
        data = await weather_service.get_weather()
        print(f"Location: {data.get('location')}")
        print(f"Forecast length: {len(data.get('forecast', []))}")
        print("Forecast items:")
        for i, item in enumerate(data.get('forecast', [])):
            print(f"  {i}: {item['display_date']} - {item['high']}° / {item['low']}° - {item['condition']}")
        
        # Try to serialize
        print("\nTesting serialization...")
        json_output = json.dumps(data)
        print("Serialization successful.")
        print(f"JSON Length: {len(json_output)}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_weather())
