import sys
import os

sys.path.append(os.getcwd())

print("Importing scheduler_service...")
try:
    from services import scheduler_service
    print("scheduler_service imported.")
except ImportError as e:
    print(f"Failed to import scheduler_service: {e}")

print("Importing altimeter_service...")
try:
    from services import altimeter_service
    print("altimeter_service imported.")
except ImportError as e:
    print(f"Failed to import altimeter_service: {e}")

print("Importing ai_service...")
try:
    from services import ai_service
    print("ai_service imported.")
except ImportError as e:
    print(f"Failed to import ai_service: {e}")

print("Importing routes...")
try:
    from api import routes
    print("routes imported.")
except ImportError as e:
    print(f"Failed to import routes: {e}")
