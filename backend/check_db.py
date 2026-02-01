
import sqlite3
import os

DB_PATH = r"C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables found:")
        for t in tables:
            print(f" - {t[0]}")
        
        # Check Projects
        try:
            cursor.execute("SELECT COUNT(*) FROM Projects")
            count = cursor.fetchone()[0]
            print(f"Project Count: {count}")
            
            if count > 0:
                cursor.execute("SELECT ProjectID, ProjectName FROM Projects LIMIT 5")
                rows = cursor.fetchall()
                for r in rows:
                    print(f" - {r}")
        except Exception as e:
            print(f"Error querying Projects: {e}")

        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    check_db()
