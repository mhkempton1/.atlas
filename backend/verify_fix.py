import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath("."))

from database.database import Base, engine, SessionLocal
from database.models import Email
from datetime import datetime

def verify_fix():
    print("Checking database schema for message_id nullability...")
    
    # Try to insert an email without a message_id
    db = SessionLocal()
    try:
        test_email = Email(
            gmail_id="test_verification_id",
            message_id=None, # This was previously causing the error
            subject="Verification Test",
            date_received=datetime.now()
        )
        db.add(test_email)
        db.commit()
        print("SUCCESS: Successfully inserted email with null message_id.")
        
        # Cleanup
        db.delete(test_email)
        db.commit()
        print("Cleanup successful.")
        return True
    except Exception as e:
        print(f"FAILURE: Could not insert email: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if verify_fix():
        sys.exit(0)
    else:
        sys.exit(1)
