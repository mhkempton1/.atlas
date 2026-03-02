import re

with open("backend/database/models.py", "r") as f:
    content = f.read()

# Make sure CalendarEvent has an 'id' or handle test logic correctly, wait, CalendarEvent uses 'event_id'
content = content.replace("    event_id = Column(Integer, primary_key=True, index=True)", "    id = Column('event_id', Integer, primary_key=True, index=True)")

with open("backend/database/models.py", "w") as f:
    f.write(content)
