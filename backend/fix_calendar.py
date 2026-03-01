import sqlite3

columns_to_add = {
    'google_calendar_id': 'TEXT',
    'calendar_id': 'TEXT',
    'title': 'TEXT',
    'description': 'TEXT',
    'start_time': 'DATETIME',
    'end_time': 'DATETIME',
    'location': 'TEXT',
    'attendees': 'TEXT',
    'is_all_day': 'BOOLEAN',
    'is_recurring': 'BOOLEAN',
    'recurrence_rule': 'TEXT',
    'project_id': 'INTEGER',
    'related_email_id': 'INTEGER',
    'is_declined': 'BOOLEAN',
    'created_at': 'DATETIME',
    'updated_at': 'DATETIME',
    'synced_at': 'DATETIME',
    'organizer': 'TEXT',
    'status': 'TEXT',
    'provider_type': 'TEXT'
}

print("Patching calendar_events...")
conn = sqlite3.connect('data/atlas.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(calendar_events)')
existing_cols = {row[1] for row in cursor.fetchall()}

for col, dtype in columns_to_add.items():
    if col not in existing_cols:
        print(f"Adding {col}...")
        try:
            cursor.execute(f"ALTER TABLE calendar_events ADD COLUMN {col} {dtype}")
        except Exception as e:
            print(f"Error adding {col}: {e}")

conn.commit()
conn.close()
print("Done.")
