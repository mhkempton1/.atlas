import sqlite3
import os

db_path = os.path.join("..", "data", "databases", "atlas.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    # try absolute
    db_path = r"C:\Users\mhkem\OneDrive\Documents\databasedev\atlas.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(emails)")
    columns = cursor.fetchall()
    print("Column info for 'emails' table:")
    for col in columns:
        print(col)
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='emails'")
    print("\nCREATE TABLE statement:")
    print(cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print(f"Error checking schema: {e}")
