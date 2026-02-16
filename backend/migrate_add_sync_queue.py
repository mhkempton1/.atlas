import sys
import os

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from database.database import engine, Base
from database.models import SyncQueue, SyncActivityLog, Task
from sqlalchemy import text

def migrate():
    print("Starting migration...")

    # 1. Create new tables
    print("Creating new tables (SyncQueue, SyncActivityLog)...")
    Base.metadata.create_all(bind=engine)

    # 2. Add columns to Task table manually (SQLite doesn't support 'IF NOT EXISTS' in ADD COLUMN well in all versions,
    # so we wrap in try/except or check first)

    with engine.connect() as conn:
        print("Checking for missing columns in 'tasks' table...")

        # Get existing columns
        result = conn.execute(text("PRAGMA table_info(tasks)"))
        existing_columns = [row[1] for row in result.fetchall()]

        columns_to_add = [
            ("sync_status", "VARCHAR DEFAULT 'synced'"),
            ("last_synced_at", "DATETIME"),
            ("etag", "VARCHAR"),
            ("remote_id", "VARCHAR")
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column '{col_name}' to 'tasks'...")
                try:
                    conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                except Exception as e:
                    print(f"Error adding {col_name}: {e}")
            else:
                print(f"Column '{col_name}' already exists.")

    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
