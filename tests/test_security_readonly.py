import sys
import os
import pytest
import sqlite3
import tempfile
import importlib
from unittest.mock import patch

# Ensure backend is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Force reload of AltimeterService to clear mocks from other tests
if 'services.altimeter_service' in sys.modules:
    del sys.modules['services.altimeter_service']

import services.altimeter_service
from services.altimeter_service import AltimeterService

class TestAltimeterSecurity:
    @pytest.fixture
    def temp_db(self):
        # Create a temp directory and db file
        with tempfile.TemporaryDirectory() as tmpdir:
            db_dir = os.path.join(tmpdir, "database")
            os.makedirs(db_dir)
            db_path = os.path.join(db_dir, "altimeter.db")

            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO projects (name) VALUES ('Project Alpha')")
            conn.commit()
            conn.close()

            yield tmpdir

    def test_readonly_enforcement(self, temp_db):
        """
        Verify that execute_read_only_query cannot modify the database
        even if the blacklist is bypassed.
        """
        # Ensure clean import again if needed
        if 'services.altimeter_service' in sys.modules:
             # Check if it's a mock
             if not hasattr(sys.modules['services.altimeter_service'], '__file__'):
                 del sys.modules['services.altimeter_service']
                 import services.altimeter_service
                 importlib.reload(services.altimeter_service)

        from services.altimeter_service import AltimeterService

        with patch("services.altimeter_service.settings") as mock_settings:
            mock_settings.ALTIMETER_PATH = temp_db

            service = AltimeterService()

            # 1. Verify we can read
            result = service.execute_read_only_query("SELECT * FROM projects")
            # If the service failed to connect/read, result might be an error dict
            if result and isinstance(result[0], dict) and "error" in result[0]:
                 pytest.fail(f"Read failed: {result[0]['error']}")

            assert len(result) == 1
            assert result[0]['name'] == 'Project Alpha'

            # 2. Attempt blacklist bypass (CREATE TABLE is not in blacklist)
            # This SHOULD fail with "attempt to write a readonly database" if fixed
            # or succeed if vulnerable.

            print("\nAttempting SQL Injection via CREATE TABLE...")
            result = service.execute_read_only_query("CREATE TABLE pwned (id int)")

            # Check if it succeeded by checking DB state
            conn = sqlite3.connect(os.path.join(temp_db, "database/altimeter.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pwned'")
            row = cursor.fetchone()
            conn.close()

            if row:
                pytest.fail("VULNERABILITY CONFIRMED: 'pwned' table was created. Read-only mode not enforced.")

            # If we get here and table wasn't created, check if it was because of an error
            # Ideally, we want to see the specific error "attempt to write a readonly database"
            # But the service swallows exceptions and returns [{"error": ...}]

            assert isinstance(result, list) and len(result) > 0 and "error" in result[0]
            error_msg = result[0]["error"]
            print(f"Caught expected error: {error_msg}")

            if "readonly" not in error_msg.lower() and "write" not in error_msg.lower():
                 # This might happen if my assumption about the error message is wrong,
                 # or if it failed for another reason (e.g. syntax).
                 # But "CREATE TABLE pwned (id int)" is valid SQL.
                 # So any other error is suspicious, but acceptable if it blocked execution.
                 pass
