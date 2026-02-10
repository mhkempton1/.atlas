import sys
import os

print("Starting import diagnosis...")
sys.path.append(os.getcwd())

try:
    print("Importing core.app...")
    from core.app import app
    print("Successfully imported core.app")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
