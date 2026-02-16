import sys
import os
import shutil
from sqlalchemy import create_engine, inspect, text, Column, Integer, String, DateTime, JSON, func
from sqlalchemy.orm import sessionmaker

# Add backend to path so we can import services
sys.path.append(os.path.dirname(__file__))

from core.config import settings
from database.database import Base

# We need to import the model class to use its metadata
# But since we are adding it in the next step, we can't import it yet if we run this script NOW.
# However, this script is meant to be run AFTER the model is added.
# So I will assume SyncHistory is available in database.models by the time this runs.
try:
    from database.models import SyncHistory
except ImportError:
    # Fallback if model not yet in file (for testing script logic without model update)
    # But for real migration, it should be there.
    print("Warning: SyncHistory model not found in database.models. Ensure models.py is updated.")
    from database.database import Base
    class SyncHistory(Base):
        __tablename__ = "sync_history"
        id = Column(Integer, primary_key=True, index=True)
        sync_type = Column(String, index=True)
        status = Column(String)
        items_synced = Column(Integer, default=0)
        error_count = Column(Integer, default=0)
        errors = Column(JSON, nullable=True)
        started_at = Column(DateTime(timezone=True), server_default=func.now())
        completed_at = Column(DateTime(timezone=True), nullable=True)

def migrate():
    print("Starting migration: Add SyncHistory Table...")

    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if os.path.exists(db_path):
            backup_path = db_path + ".bak"
            print(f"Backing up database to {backup_path}...")
            try:
                shutil.copy2(db_path, backup_path)
            except Exception as e:
                print(f"Failed to backup database: {e}")
                return

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_name = SyncHistory.__tablename__

    if table_name not in inspector.get_table_names():
        print(f"Table '{table_name}' is missing. Creating...")
        SyncHistory.__table__.create(engine)
        print(f"Table '{table_name}' created successfully.")
    else:
        print(f"Table '{table_name}' exists. Checking for missing columns...")
        # (Simple column check logic similar to existing migrations)
        existing_columns = {c['name'] for c in inspector.get_columns(table_name)}
        for col in SyncHistory.__table__.columns:
            if col.name not in existing_columns:
                print(f"Column '{col.name}' is missing. Adding...")
                col_type = col.type.compile(engine.dialect)
                stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"
                try:
                    with engine.connect() as conn:
                        conn.execute(text(stmt))
                    print(f"Added column '{col.name}'")
                except Exception as e:
                    print(f"Failed to add column '{col.name}': {e}")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
