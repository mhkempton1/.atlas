import sys
import os
import shutil
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add backend to path so we can import services
sys.path.append(os.path.dirname(__file__))

from core.config import settings
from database.models import Task
from database.database import Base

def migrate():
    print("Starting migration: Update Tasks Table...")

    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")

    # 1. Check existence and Backup
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")

        # Check if database exists
        if not os.path.exists(db_path):
            print(f"⚠️  Database file {db_path} not found. Skipping migration (tables will be created on next startup).")
            return

        # Backup
        backup_path = db_path + ".bak_tasks_migration"
        print(f"Backing up database to {backup_path}...")
        try:
            shutil.copy2(db_path, backup_path)
        except Exception as e:
            print(f"Failed to backup database: {e}")
            print("Aborting migration due to backup failure.")
            return

    else:
        print("Not using SQLite file path. Skipping file backup.")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    table_name = Task.__tablename__

    # 2. Check if table exists
    if table_name not in inspector.get_table_names():
        print(f"Table '{table_name}' is missing. Creating...")
        Task.__table__.create(engine)
        print(f"Table '{table_name}' created successfully.")
    else:
        print(f"Table '{table_name}' exists. Checking for missing columns...")

        existing_columns = {c['name'] for c in inspector.get_columns(table_name)}
        model_columns = Task.__table__.columns

        with engine.connect() as conn:
            for col in model_columns:
                if col.name not in existing_columns:
                    print(f"Column '{col.name}' is missing. Adding...")

                    # Compile column type for SQLite
                    col_type = col.type.compile(engine.dialect)

                    # Handle nullable/defaults for existing rows
                    # SQLite ADD COLUMN usually requires default if NOT NULL, but these are nullable or have defaults

                    # Construct ALTER TABLE statement
                    stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"

                    try:
                        conn.execute(text(stmt))
                        print(f"Added column '{col.name}'")
                    except Exception as e:
                        print(f"Failed to add column '{col.name}': {e}")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
