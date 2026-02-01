import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'c:/Users/mhkem/.atlas/backend'))

print("Testing imports...")
try:
    from services.scheduler_service import SchedulerService
    print("SchedulerService imported successfully")
except Exception as e:
    print(f"FAILED to import SchedulerService: {e}")
    import traceback
    traceback.print_exc()

try:
    from services.scheduler_service import scheduler_service
    print("Instance scheduler_service imported successfully")
except Exception as e:
    print(f"FAILED to import instance: {e}")
