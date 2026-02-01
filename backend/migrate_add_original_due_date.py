"""
Database migration script to add missing original_due_date column to tasks table.
Run this script to fix the schema issue.
"""
import sqlite3
import os
from pathlib import Path

# Database path from backend config
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
db_path = DATA_DIR / "databases" / "atlas.db"

print(f"📂 Using database at: {db_path}")

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    exit(1)

print(f"📂 Found database at: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'original_due_date' in columns:
        print("✅ Column 'original_due_date' already exists!")
    else:
        print("🔧 Adding 'original_due_date' column to tasks table...")
        
        # Add the column (SQLite doesn't support adding columns with default values in one step)
        cursor.execute("ALTER TABLE tasks ADD COLUMN original_due_date TEXT")
        
        # Set original_due_date to due_date for existing tasks
        cursor.execute("UPDATE tasks SET original_due_date = due_date WHERE original_due_date IS NULL")
        
        conn.commit()
        print("✅ Successfully added 'original_due_date' column!")
        print("✅ Populated existing tasks with their current due_date as original_due_date")
    
    # Verify the change
    cursor.execute("PRAGMA table_info(tasks)")
    print("\n📋 Current tasks table schema:")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
except Exception as e:
    print(f"❌ Error during migration: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

print("\n🎉 Migration complete! You can now restart the backend.")
