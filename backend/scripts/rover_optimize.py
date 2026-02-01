
import os
import time
import sqlite3
import requests
import statistics
from datetime import datetime

# Configuration
API_BASE = "http://localhost:4201/api/v1"
DB_PATH = r"C:\Users\mhkem\OneDrive\Documents\databasedev\atlas.db"

def benchmark_endpoint(name, path, method="GET", json=None):
    url = f"{API_BASE}{path}"
    latencies = []
    print(f"[*] Benchmarking {name} ({path})...")
    
    for _ in range(3):
        start = time.perf_counter()
        try:
            if method == "GET":
                res = requests.get(url, timeout=5)
            else:
                res = requests.post(url, json=json, timeout=5)
            
            latency = (time.perf_counter() - start) * 1000
            if res.status_code == 200:
                latencies.append(latency)
            else:
                print(f"  [!] Received non-200 status: {res.status_code}")
        except Exception as e:
            print(f"  [!] Request failed: {e}")
    
    if latencies:
        avg = statistics.mean(latencies)
        print(f"  [+] Avg Latency: {avg:.2f}ms")
        return avg
    return None

def check_database():
    print("[*] Checking Database Health...")
    if not os.path.exists(DB_PATH):
        print(f"  [!] Database not found at {DB_PATH}")
        return
    
    size = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"  [+] DB Size: {size:.2f} MB")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check for missing indexes on common query columns
    tables = ['tasks', 'emails', 'calendar_events']
    for table in tables:
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        print(f"  [+] Table '{table}' has {len(indexes)} indexes")

    # Perform VACUUM
    print("[*] Performing Database Maintenance (VACUUM)...")
    start = time.perf_counter()
    conn.execute("VACUUM")
    print(f"  [+] Maintenance complete in {(time.perf_counter() - start):.2f}s")
    
    conn.close()

def main():
    print("="*40)
    print(" ATLAS ROVER PERFORMANCE OPTIMIZER ")
    print("="*40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # 1. API Benchmarks
    results = {}
    results['health'] = benchmark_endpoint("Health Check", "/health")
    results['stats'] = benchmark_endpoint("Dashboard Stats", "/dashboard/stats")
    results['tasks'] = benchmark_endpoint("Task Listing", "/tasks/list")
    results['emails'] = benchmark_endpoint("Email Listing", "/email/list")
    
    # 2. DB Ops
    check_database()
    
    # 3. Recommendations
    print("\n" + "="*40)
    print(" ROVER RECOMMENDATIONS ")
    print("="*40)
    
    if results.get('stats') and results['stats'] > 200:
        print("[!] Dashboard stats are slow (>200ms). Consider caching the results.")
    
    if results.get('emails') and results['emails'] > 300:
        print("[!] Email listing is slow (>300ms). Check if indexes exist on 'date_received'.")

    print("[+] All systems calibrated. Speed optimization complete.")

if __name__ == "__main__":
    main()
