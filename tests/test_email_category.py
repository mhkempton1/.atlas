import sys
import os
import asyncio
from datetime import datetime

# Add path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
sys.path.append(os.path.join(root_path, "backend"))

from backend.database.database import SessionLocal
from backend.database.models import Email
from backend.api.email_routes import update_category, CategoryUpdate

async def test_category_update():
    print("=== TESTING EMAIL CATEGORY UPDATE ===\n")
    
    db = SessionLocal()
    try:
        # 1. Create a dummy email
        new_email = Email(
            subject="Test Category Email",
            from_address="test@example.com",
            body_text="Testing categories",
            date_received=datetime.now(),
            message_id="test_cat_123",
            category="inbox"
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)
        
        email_id = new_email.email_id
        print(f"Created Test Email ID: {email_id} with category: {new_email.category}")
        
        # 2. Update category
        print("Updating category to 'work'...")
        update_req = CategoryUpdate(category="work")
        
        await update_category(email_id=email_id, update=update_req, db=db)
        
        # 3. Verify
        db.refresh(new_email)
        print(f"Updated Category: {new_email.category}")
        
        if new_email.category == "work":
            print("[SUCCESS] Category updated successfully.")
        else:
            print(f"[FAILED] Expected 'work', got '{new_email.category}'")
            
        # Cleanup
        db.delete(new_email)
        db.commit()
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_category_update())
