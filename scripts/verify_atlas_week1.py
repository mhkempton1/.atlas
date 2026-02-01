import sys
import os
import sqlite3
from sqlalchemy import create_engine, inspect

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.config import settings
from database.models import Base, Email, CalendarEvent
from services.google_service import google_service

def verify_database():
    print("\n--- Verifying Database ---")
    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")
    
    # Check file existence if sqlite
    if "sqlite" in db_url:
        path = db_url.replace("sqlite:///", "")
        if os.path.exists(path):
            print(f"✅ Database file exists at {path}")
        else:
            print(f"❌ Database file NOT found at {path} (Will be created on app startup)")
            
    # Check tables
    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['emails', 'email_attachments', 'contacts', 'tasks', 'calendar_events', 'drafts']
        missing = [t for t in expected_tables if t not in tables]
        
        if not missing:
            print(f"✅ All expected tables found: {tables}")
        else:
            print(f"❌ Missing tables: {missing}")
            print(f"Found: {tables}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def verify_google_service():
    print("\n--- Verifying Google Service (Gmail + Calendar) ---")
    
    if google_service.gmail_service:
        print("✅ Gmail Service active")
    else:
        print("⚠️ Gmail Service NOT active")
        
    if google_service.calendar_service:
        print("✅ Calendar Service active")
    else:
        print("⚠️ Calendar Service NOT active")
        
    if google_service.gmail_service:
        print("Attempting to sync calendar (Requires re-auth if scope changed)...")
        try:
             res = google_service.sync_calendar()
             print(f"✅ Calendar Sync Successful: {res}")
        except Exception as e:
             print(f"⚠️ Calendar Sync Warning: {e}")
             print("Note: If you see 'Insufficient Permission', you need to delete the vault token and re-authenticate.")

if __name__ == "__main__":
    verify_database()
    verify_google_service()
