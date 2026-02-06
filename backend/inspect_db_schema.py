import sqlite3
import os

db_path = "atlas.db"
print(f"Inspecting LOCAL DB: {os.path.abspath(db_path)}")

if not os.path.exists(db_path):
    print("DB file not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    output = []
    output.append("\n--- calendar_events columns ---")
    cursor.execute("PRAGMA table_info(calendar_events)")
    columns = cursor.fetchall()
    for col in columns:
        output.append(f"ID: {col[0]}, Name: {col[1]}, Type: {col[2]}")
        
    output.append("\n--- All tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        output.append(table[0])
        
    with open("db_schema.txt", "w") as f:
        f.write("\n".join(output))
    print("Schema written to db_schema.txt")
        
    conn.close()
except Exception as e:
    print(f"Inspection failed: {e}")
