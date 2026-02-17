from database.database import engine, Base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime, timezone
from sqlalchemy.sql import func

class SyncConflict(Base):
    __tablename__ = "sync_conflicts"
    __extend_existing__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    local_version = Column(JSON, nullable=False)
    remote_version = Column(JSON, nullable=False)
    status = Column(String(20), default='unresolved')
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def run_migration():
    print("Creating sync_conflicts table...")
    try:
        SyncConflict.__table__.create(engine, checkfirst=True)
        print("Migration complete.")
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    run_migration()
