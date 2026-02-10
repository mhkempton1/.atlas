import sqlite3
from sqlalchemy import create_engine, text
from core.config import settings
import os

db_path = settings.DATABASE_URL.replace("sqlite:///", "")
print(f"Inspecting DB Path: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    output = []
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        output.append(f"\n--- TABLE: {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            output.append(f"  Col ID: {col[0]}, Name: {col[1]}, Type: {col[2]}")
            
    with open("full_db_schema.txt", "w") as f:
        f.write("\n".join(output))
    print("Full schema written to full_db_schema.txt")
    
    conn.close()
except Exception as e:
    print(f"Inspection failed: {e}")
