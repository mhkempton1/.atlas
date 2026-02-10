from sqlalchemy import create_engine, text
from core.config import settings
import os

print(f"Engine connecting to: {settings.DATABASE_URL}")
engine = create_engine(settings.DATABASE_URL)

try:
    with engine.connect() as conn:
        print("\n--- Raw PRAGMA table_info ---")
        result = conn.execute(text("PRAGMA table_info(calendar_events)"))
        for row in result:
            print(row)
            
        print("\n--- Raw Tables ---")
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        for row in result:
            print(row)
except Exception as e:
    print(f"PRAGMA failed: {e}")
