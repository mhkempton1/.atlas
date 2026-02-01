import chromadb
import os

persist_path = r"C:\Users\mhkem\OneDrive\Documents\databasedev\vectors"
print(f"Attempting to connect to ChromaDB at: {persist_path}")

try:
    client = chromadb.PersistentClient(path=persist_path)
    print("Successfully connected!")
    collections = client.list_collections()
    print(f"Collections: {[c.name for c in collections]}")
except Exception as e:
    print(f"Caught Exception: {e}")
except BaseException as e:
    print(f"Caught BaseException (Panic?): {e}")
