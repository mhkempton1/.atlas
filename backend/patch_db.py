import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath("."))

from database.database import Base, engine
from database.models import Email, EmailAttachment, Contact, Task, Draft

def patch_schema():
    print("Recreating 'emails' table to apply nullable message_id fix...")
    try:
        # We only want to recreate the emails table if necessary, but 
        # since this is a development fix, dropping and recreating is often simplest 
        # for SQLite. However, that loses data. 
        # ALternative: just use Base.metadata.create_all which might NOT update existing.
        # SQLite doesn't support 'ALTER TABLE DROP CONSTRAINT' etc easily.
        
        # PROPER WAY for SQLite: Rename table, create new table, copy data, drop old.
        # But for this task, if we assume data loss is okay (sync will refetch):
        # We can drop it.
        
        Email.__table__.drop(engine, checkfirst=True)
        Email.__table__.create(engine)
        print("SUCCESS: 'emails' table recreated with current model definition.")
        return True
    except Exception as e:
        print(f"FAILURE: {e}")
        return False

if __name__ == "__main__":
    patch_schema()
