import sys
import os
import api.routes
import services.altimeter_service

print(f"PYTHONPATH: {sys.path}")
print(f"api.routes file: {api.routes.__file__}")
print(f"services.altimeter_service file: {services.altimeter_service.__file__}")
