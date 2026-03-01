import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from agents.project_agent import project_agent
import logging

logging.basicConfig(level=logging.INFO)

async def run_test():
    print("Testing Project Agent Draft Creation...")
    ctx = {
        'action': 'draft_daily_log',
        'project_id': 'General', # Fallback test project
        'user_prompt': 'Please mention that we finished the rough-in on the 2nd floor today and everything went smoothly.'
    }
    result = await project_agent.process(ctx)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(run_test())
