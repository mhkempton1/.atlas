import sys
import os
import shutil
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add backend to path so we can import services
sys.path.append(os.path.dirname(__file__))

from core.config import settings
from database.models import CalendarEvent
from database.database import Base

def migrate():
    print("Starting migration: Update Calendar Events Table...")

    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            print(f"⚠️  Database file {db_path} not found. Skipping migration (tables will be created on next startup).")
            return

        # Backup
        backup_path = db_path + ".bak_calendar_migration"
        print(f"Backing up database to {backup_path}...")
        try:
            shutil.copy2(db_path, backup_path)
        except Exception as e:
            print(f"Failed to backup database: {e}")
            print("Aborting migration due to backup failure.")
            return

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_name = "calendar_events"

    if table_name not in inspector.get_table_names():
        print(f"Table '{table_name}' does not exist. Creating new table...")
        CalendarEvent.__table__.create(engine)
        print("Table created.")
        return

    # Check if migration is needed (check if 'google_calendar_id' exists)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    if "google_calendar_id" in columns and "id" in columns and "is_all_day" in columns:
        print("Table seems to be already migrated.")
        return

    print("Migrating table schema...")

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Rename existing table
            print("Renaming existing table to 'calendar_events_old'...")
            conn.execute(text(f"ALTER TABLE {table_name} RENAME TO {table_name}_old"))

            # 2. Create new table
            print("Creating new 'calendar_events' table...")
            CalendarEvent.__table__.create(conn)

            # 3. Copy data
            print("Copying data...")
            # We need to list columns to select from old table and insert into new table
            # Old columns: event_id, remote_event_id, provider_type, calendar_id, title, description, location, start_time, end_time, all_day, attendees, organizer, status, project_id, created_at, updated_at, synced_at

            # Get columns from old table to be sure
            old_columns_info = inspect(conn).get_columns(f"{table_name}_old")
            old_columns = [c['name'] for c in old_columns_info]

            # Mapping
            # id <- event_id
            # google_calendar_id <- remote_event_id
            # is_all_day <- all_day
            # others same

            # Construct SELECT statement
            select_cols = []
            insert_cols = []

            mapping = {
                "event_id": "id",
                "remote_event_id": "google_calendar_id",
                "all_day": "is_all_day"
            }

            for old_col in old_columns:
                new_col = mapping.get(old_col, old_col)
                # Check if new_col exists in new table (it should)
                if new_col in CalendarEvent.__table__.columns:
                    select_cols.append(old_col)
                    insert_cols.append(new_col)

            select_str = ", ".join(select_cols)
            insert_str = ", ".join(insert_cols)

            stmt = f"INSERT INTO {table_name} ({insert_str}) SELECT {select_str} FROM {table_name}_old"
            conn.execute(text(stmt))

            # 4. Drop old table
            print("Dropping 'calendar_events_old'...")
            conn.execute(text(f"DROP TABLE {table_name}_old"))

            trans.commit()
            print("Migration successful.")

        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")
            # Restore from backup if needed manually, or we could automate restoration here
            print("Transaction rolled back.")
            raise e

if __name__ == "__main__":
    migrate()
