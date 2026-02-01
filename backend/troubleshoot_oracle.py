import sys
import os
import asyncio
import httpx
from datetime import datetime

# Add the directory containing core to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def diagnose_oracle():
    print(f"--- Oracle Protocol Diagnostics ({datetime.now().strftime('%H:%M:%S')}) ---")
    
    from services.altimeter_service import altimeter_service, intelligence_bridge
    from services.weather_service import weather_service
    
    # 1. Check Altimeter Phases
    print("[1/3] Fetching Active Phases...")
    phases = altimeter_service.get_active_phases()
    if not phases:
        print("  ! No active phases found in Altimeter DB.")
    else:
        print(f"  > Found {len(phases)} active phases.")
        for p in phases:
            print(f"    - {p['phase_name']} (Project: {p['project_id']})")
            
    # 2. Check Weather Service
    print("\n[2/3] Fetching Weather Context...")
    weather = await weather_service.get_weather()
    print(f"  > Condition: {weather.get('current', {}).get('condition', 'Unknown')}")
    print(f"  > Summary: {weather.get('location', 'Nixa, MO')}")
    
    # 3. Test Prediction
    print("\n[3/3] Running Oracle Prediction Logic...")
    intel = intelligence_bridge.predict_mission_intel(phases, weather)
    if not intel:
        print("  ! No Mission Intel generated.")
    else:
        print(f"  > Detected {len(intel)} Intelligence Items:")
        for item in intel:
            print(f"    [*] {item['trigger']} -> {item['title']} (Relevance: {item['relevance']:.2f})")
            print(f"        Snippet: {item['snippet'][:80]}...")
            
    print("\n--- Diagnostic Complete ---")

if __name__ == "__main__":
    asyncio.run(diagnose_oracle())
