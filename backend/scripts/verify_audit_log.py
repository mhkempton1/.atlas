import sys
import os
import json
import time
import asyncio
from unittest.mock import MagicMock

# Add backend to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Ensure TEST env var is NOT set for the first part
if "TEST" in os.environ:
    del os.environ["TEST"]

from backend.services.ai_service import ai_service
from backend.core.config import settings

LOG_DIR = os.path.join(os.getcwd(), "backend", "data")
LOG_FILE = os.path.join(LOG_DIR, "ai_audit_log.jsonl")

def setup():
    # Clean up existing logs
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    if os.path.exists(LOG_FILE.replace(".jsonl", ".1.jsonl")):
        os.remove(LOG_FILE.replace(".jsonl", ".1.jsonl"))

    # Mock the client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked AI Response"
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.total_token_count = 123

    mock_client.models.generate_content.return_value = mock_response

    ai_service.client = mock_client
    ai_service.model_name = "mock-gemini-model"

    return mock_client

async def verify_basic_logging():
    print("Verifying basic logging...")
    mock_client = setup()

    await ai_service.generate_content("Test Prompt")

    if not os.path.exists(LOG_FILE):
        print("FAIL: Log file not created")
        return False

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    if len(lines) != 1:
        print(f"FAIL: Expected 1 log line, found {len(lines)}")
        return False

    entry = json.loads(lines[0])

    expected_fields = ["timestamp", "prompt", "response", "model", "tokens_used", "latency_ms", "status"]
    for field in expected_fields:
        if field not in entry:
            print(f"FAIL: Missing field {field} in log entry")
            return False

    if entry["prompt"] != "Test Prompt":
        print(f"FAIL: Expected prompt 'Test Prompt', got '{entry['prompt']}'")
        return False

    if entry["response"] != "Mocked AI Response":
        print(f"FAIL: Expected response 'Mocked AI Response', got '{entry['response']}'")
        return False

    if entry["status"] != "success":
        print(f"FAIL: Expected status 'success', got '{entry['status']}'")
        return False

    if entry["tokens_used"] != 123:
        print(f"FAIL: Expected tokens_used 123, got {entry['tokens_used']}")
        return False

    print("PASS: Basic logging verified")
    return True

async def verify_error_logging():
    print("Verifying error logging...")
    mock_client = setup()

    # Simulate error
    mock_client.models.generate_content.side_effect = Exception("Simulated API Error")

    await ai_service.generate_content("Error Prompt")

    if not os.path.exists(LOG_FILE):
        print("FAIL: Log file not created on error")
        return False

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    entry = json.loads(lines[0])

    if entry["status"] != "error":
        print(f"FAIL: Expected status 'error', got '{entry['status']}'")
        return False

    if "error_message" not in entry or "Simulated API Error" not in entry["error_message"]:
        print(f"FAIL: Expected error message 'Simulated API Error', got '{entry.get('error_message')}'")
        return False

    print("PASS: Error logging verified")
    return True

async def verify_log_rotation():
    print("Verifying log rotation...")
    setup() # Clear logs

    # Create a dummy large file (simulating > 50MB)
    # We'll just create a file slightly larger than 50MB
    # Wait, creating 50MB file takes time and space.
    # Maybe I can mock the size check?
    # No, I should test the logic.
    # But writing 50MB is fast enough.

    large_content = "x" * (50 * 1024 * 1024 + 100) # 50MB + 100 bytes

    # Ensure directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    with open(LOG_FILE, "w") as f:
        f.write(large_content)

    # Trigger log
    mock_client = setup() # This clears logs... wait!
    # Setup clears logs. I need to modify setup or just do it manually here.

    # Re-mock without clearing
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Response after rotation"
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.total_token_count = 123
    mock_client.models.generate_content.return_value = mock_response
    ai_service.client = mock_client

    # Manually recreate the large file because setup() deleted it
    with open(LOG_FILE, "w") as f:
        f.write(large_content)

    await ai_service.generate_content("Rotation Prompt")

    rotated_file = LOG_FILE.replace(".jsonl", ".1.jsonl")
    if not os.path.exists(rotated_file):
        print("FAIL: Rotated file not created")
        return False

    # Check size of rotated file
    if os.path.getsize(rotated_file) < 50 * 1024 * 1024:
        print("FAIL: Rotated file size is too small")
        return False

    # Check new log file exists and is small
    if not os.path.exists(LOG_FILE):
        print("FAIL: New log file not created")
        return False

    if os.path.getsize(LOG_FILE) > 1024:
        print("FAIL: New log file is too large (should be just one entry)")
        return False

    with open(LOG_FILE, "r") as f:
        content = f.read()
        if "Rotation Prompt" not in content:
            print("FAIL: New log file does not contain new entry")
            return False

    print("PASS: Log rotation verified")
    return True

async def verify_test_mode():
    print("Verifying test mode skipped logging...")
    setup()

    os.environ["TEST"] = "true"

    await ai_service.generate_content("Test Mode Prompt")

    if os.path.exists(LOG_FILE):
        print("FAIL: Log file created in TEST mode")
        return False

    print("PASS: Test mode verified")
    del os.environ["TEST"]
    return True

async def main():
    try:
        if not await verify_basic_logging():
            sys.exit(1)
        if not await verify_error_logging():
            sys.exit(1)
        if not await verify_log_rotation():
            sys.exit(1)
        if not await verify_test_mode():
            sys.exit(1)
        print("\nALL VERIFICATIONS PASSED")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
