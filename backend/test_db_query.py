from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from database.models import CalendarEvent
from core.config import settings
from datetime import datetime, timedelta

print(f"Connecting to: {settings.DATABASE_URL}")
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Querying events starting after: {today_start}")
    
    # Attempting the exact query
    events = session.query(CalendarEvent).filter(
        CalendarEvent.start_time >= today_start
    ).all()
    
    print(f"Success! Found {len(events)} events.")
except Exception as e:
    print(f"Query failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
