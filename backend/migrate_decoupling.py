import sqlite3
import os

def migrate_db():
    db_path = r"C:/Users/mhkem/OneDrive/Documents/databasedev/atlas.db"
    if not os.path.exists(db_path):
        print("Database not found. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting Database Migration: The Great Decoupling...")
        
        # 1. Update Emails table
        cursor.execute("ALTER TABLE emails RENAME COLUMN gmail_id TO remote_id;")
        cursor.execute("ALTER TABLE emails ADD COLUMN provider_type TEXT DEFAULT 'google';")
        
        # 2. Update Calendar Events table
        cursor.execute("ALTER TABLE calendar_events RENAME COLUMN google_event_id TO remote_event_id;")
        cursor.execute("ALTER TABLE calendar_events ADD COLUMN provider_type TEXT DEFAULT 'google';")
        
        # 3. Update Email Attachments table
        cursor.execute("ALTER TABLE email_attachments RENAME COLUMN gmail_attachment_id TO remote_attachment_id;")
        
        conn.commit()
        print("Migration COMPLETED: Database is now provider-agnostic.")
    except Exception as e:
        print(f"Migration FAILED: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
