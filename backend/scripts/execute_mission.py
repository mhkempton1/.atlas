import asyncio
import argparse
import sys
import os

# Add backend to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.ai_service import ai_service
from services.communication_service import comm_service
from services.altimeter_service import altimeter_service

async def run_mission(mission_prompt: str, mission_type: str):
    print(f"🚀 Starting Mission: {mission_type}")
    print(f"📝 Prompt: {mission_prompt[:100]}...")

    # 1. Inject specialized context based on mission type
    context_data = ""
    if "email" in mission_type:
        print("   - Syncing latest emails...")
        try:
            comm_service.sync_emails(limit=20)
            context_data += "\n[System Log] Emails synced successfully."
        except Exception as e:
            context_data += f"\n[System Log] Email sync warning: {e}"

    if "calendar" in mission_type:
         print("   - Syncing calendar...")
         # comm_service.sync_calendar() 
         pass

    # 2. Execute the prompt via Gemini
    print("   - Consulting The Oracle (Gemini)...")
    full_prompt = f"{mission_prompt}\n\n[SYSTEM UPDATE]\n{context_data}"
    
    response = await ai_service.generate_content(full_prompt, include_context=True)

    if response:
        print("✅ Mission Accomplished.")
        print("==========================================")
        print(response)
        print("==========================================")
        
        # In a real agentic loop, we would parse 'response' for tool calls here.
        # For now, we trust the agent to output a 'System Log' or 'Plan'.
    else:
        print("❌ Mission Failed: No response from AI.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Execute an autonomous mission.')
    parser.add_argument('--prompt', required=True, help=' The mission prompt for the AI')
    parser.add_argument('--type', default='general', help='Type of mission (email, calendar, maintenance)')
    
    args = parser.parse_args()
    
    asyncio.run(run_mission(args.prompt, args.type))
