import sys
import os
import pytest
import asyncio
from unittest.mock import MagicMock
from datetime import datetime

# Add project root and backend to path for imports
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
sys.path.append(os.path.join(root_path, "backend"))

# Use consistent imports
from database.database import SessionLocal, engine, Base
from database.models import Email, TaskQueue
from api.email_routes import scan_emails, run_background_scan
from services.google_service import google_service
from services.ai_service import ai_service

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Mock sync to avoid hitting real Gmail
google_service.sync_emails = MagicMock(return_value={"synced": 0})

# Return a valid JSON string that the TaskAgent expects
ai_service.generate_content = MagicMock(return_value='''
{
    "tasks": [
        {
            "title": "Fix Wiring",
            "description": "Fix the wiring at Innovation Hub",
            "priority": "High",
            "due_date": null
        }
    ]
}
''')

@pytest.mark.asyncio
async def test_integration():
    print("=== TESTING ATLAS <-> ALTIMETER INTEGRATION (REFACTORED) ===")
    
    db = SessionLocal()
    try:
        # 1. Cleanup old test data
        try:
            db.query(Email).filter(Email.subject == "URGENT: Issue with 25-9999-TEST").delete(synchronize_session=False)
            db.query(TaskQueue).filter(TaskQueue.type == "analyze_email").delete(synchronize_session=False)
            db.commit()
        except:
            pass # Tables might be fresh

        # 2. Seed Test Email
        print("Step 1: Seeding DB with Test Email...")
        test_email = Email(
            message_id="test-msg-123456",
            gmail_id="test-gmail-123456",
            from_address="bob@builder.com",
            subject="URGENT: Issue with 25-9999-TEST",
            body_text="We need help with the wiring at the Innovation Hub. 25-9999. Attached is RFI.",
            date_received=datetime.now(),
            is_read=False,
            is_starred=False,
            synced_at=datetime.now()
        )
        db.add(test_email)
        db.commit()
        
        # 3. Run Scan
        print("Step 2: Running Atlas Email Scan...")
        bg_tasks = MagicMock()
        result = await scan_emails(background_tasks=bg_tasks, limit=5, db=db)

        # Verify API response is empty (async pattern)
        assert result.emails_found == 0
        
        # Verify background task scheduled
        args, _ = bg_tasks.add_task.call_args
        assert args[0] == run_background_scan
        
        print("Step 3: Triggering background logic manually...")
        # Manually run the background task logic to verify queuing
        run_background_scan(limit=5)
        
        # 4. Verify TaskQueue has item
        print("Step 4: Verifying Task Queue...")
        queue_item = db.query(TaskQueue).filter(
            TaskQueue.type == "analyze_email"
        ).order_by(TaskQueue.id.desc()).first()

        assert queue_item is not None
        assert queue_item.payload['subject'] == "URGENT: Issue with 25-9999-TEST"
        assert queue_item.status == "pending"

        print("SUCCESS: Scan scheduled and task queued correctly.")

    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        # Cleanup
        try:
            db.query(Email).filter(Email.subject == "URGENT: Issue with 25-9999-TEST").delete(synchronize_session=False)
            db.commit()
        except:
            pass
        db.close()

if __name__ == "__main__":
    try:
        asyncio.run(test_integration())
    except KeyboardInterrupt:
        pass
