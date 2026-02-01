from sqlalchemy import create_engine, text
import os

DB_PATH = r"C:\Users\mhkem\OneDrive\Documents\databasedev\altimeter.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        with engine.connect() as conn:
            # List Tables
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
            print("Tables found:")
            for t in tables:
                print(f"- {t[0]}")
                
            # For each table, list columns
            for t in tables:
                table_name = t[0]
                print(f"\nSchema for {table_name}:")
                cols = conn.execute(text(f"PRAGMA table_info({table_name});")).fetchall()
                for c in cols:
                    print(f"  {c[1]} ({c[2]})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
