import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.scheduler_service import morning_briefing_job
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Testing Morning Briefing Generation...")
    # This invokes the AI summarization, weather fetching, and email sending
    morning_briefing_job()
    print("Test finished. Please check michael@daviselectric.biz for the email.")
