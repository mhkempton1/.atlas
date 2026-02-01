import sqlite3
import os

db_path = r"C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db"

print(f"Checking Altimeter DB at: {db_path}")
if not os.path.exists(db_path):
    print(f"❌ DB File not found!")
else:
    print(f"✅ DB File exists.")
    try:
        conn = sqlite3.connect(db_path)
        print("✅ Connection established.")
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM projects WHERE is_active = 1")
        count = cursor.fetchone()[0]
        print(f"✅ Query successful. Active projects: {count}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
