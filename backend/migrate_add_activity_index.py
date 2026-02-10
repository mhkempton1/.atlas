"""
Database migration script to add an index to the SystemActivity.timestamp column.
This improves performance for the activity feed queries.
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
    print(f"⚠️ Database not found at {db_path}. Skipping migration (will be created with index on next startup).")
    exit(0)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("🔧 Adding index to system_activity.timestamp...")

    # Create the index if it doesn't exist
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_system_activity_timestamp ON system_activity (timestamp)")

    conn.commit()
    print("✅ Successfully added index 'ix_system_activity_timestamp'!")

    # Verify the index exists
    cursor.execute("PRAGMA index_list(system_activity)")
    indexes = cursor.fetchall()
    print("\n📋 Current system_activity indexes:")
    for idx in indexes:
        print(f"  - {idx[1]}")

except Exception as e:
    print(f"❌ Error during migration: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

print("\n🎉 Migration complete!")
