import sys
import os
from sqlalchemy import create_engine

# Add backend to path so we can import services
sys.path.append(os.path.dirname(__file__))

from core.config import settings
from database.models import Contact

def migrate():
    print("Starting migration: Update Contacts Schema...")

    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")

    engine = create_engine(db_url)

    print("Dropping 'contacts' table if it exists...")
    try:
        Contact.__table__.drop(engine, checkfirst=True)
        print("Dropped 'contacts' table.")
    except Exception as e:
        print(f"Error dropping table: {e}")
        return

    print("Creating 'contacts' table with new schema...")
    try:
        Contact.__table__.create(engine)
        print("Created 'contacts' table successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
        return

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
