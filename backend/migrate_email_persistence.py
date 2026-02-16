import sys
import os
from sqlalchemy import create_engine, inspect, text

# Add backend to path so we can import services
sys.path.append(os.path.dirname(__file__))

from core.config import settings
from database.models import Email, EmailAttachment
from database.database import Base

def migrate():
    print("Starting migration: Add Email Persistence Fields...")

    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")

    if not db_url:
        print("Database URL not configured.")
        return

    # Connect to DB
    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    # 1. Update Email Table
    table_name = Email.__tablename__
    if table_name in inspector.get_table_names():
        print(f"Table '{table_name}' exists. Checking for missing columns...")
        existing_columns = {c['name'] for c in inspector.get_columns(table_name)}

        # New columns to check
        new_columns = ['gmail_id', 'sender', 'recipients', 'is_unread', 'archived_at', 'deleted_at']

        with engine.connect() as conn:
            for col in Email.__table__.columns:
                if col.name in new_columns and col.name not in existing_columns:
                    print(f"Column '{col.name}' is missing in '{table_name}'. Adding...")
                    # Compile type
                    col_type = col.type.compile(engine.dialect)
                    stmt = text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")
                    try:
                        conn.execute(stmt)
                        print(f"Added column '{col.name}' to '{table_name}'")
                    except Exception as e:
                        print(f"Failed to add column '{col.name}': {e}")
            conn.commit()
    else:
        print(f"Table '{table_name}' does not exist. It will be created by init_db or usage.")

    # 2. Update EmailAttachment Table
    table_name = EmailAttachment.__tablename__
    if table_name in inspector.get_table_names():
        print(f"Table '{table_name}' exists. Checking for missing columns...")
        existing_columns = {c['name'] for c in inspector.get_columns(table_name)}

        # New columns to check
        new_columns = ['storage_path']

        with engine.connect() as conn:
            for col in EmailAttachment.__table__.columns:
                if col.name in new_columns and col.name not in existing_columns:
                    print(f"Column '{col.name}' is missing in '{table_name}'. Adding...")
                    col_type = col.type.compile(engine.dialect)
                    stmt = text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")
                    try:
                        conn.execute(stmt)
                        print(f"Added column '{col.name}' to '{table_name}'")
                    except Exception as e:
                        print(f"Failed to add column '{col.name}': {e}")
            conn.commit()
    else:
        print(f"Table '{table_name}' does not exist.")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
