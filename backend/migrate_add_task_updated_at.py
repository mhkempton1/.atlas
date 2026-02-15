import sqlite3
import os
from pathlib import Path

# Assuming running from repo root
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "atlas.db"

def migrate():
    print(f"Checking database at: {DB_PATH}")

    if not DATA_DIR.exists():
        print(f"Directory {DATA_DIR} does not exist. Creating...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        print("Database file does not exist. It will be created by the application on startup with the new schema.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if tasks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if not cursor.fetchone():
            print("Table 'tasks' does not exist. It will be created by the application.")
            return

        # Get existing columns
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]

        # 1. Add updated_at
        if "updated_at" in columns:
            print("Column 'updated_at' already exists in 'tasks'.")
        else:
            print("Adding column 'updated_at' to 'tasks'...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN updated_at DATETIME")
            print("Column 'updated_at' added successfully.")

        # 2. Add related_altimeter_task_id
        if "related_altimeter_task_id" in columns:
            print("Column 'related_altimeter_task_id' already exists in 'tasks'.")
        else:
            print("Adding column 'related_altimeter_task_id' to 'tasks'...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN related_altimeter_task_id VARCHAR")
            print("Column 'related_altimeter_task_id' added successfully.")

        conn.commit()

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
