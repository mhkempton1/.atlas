
import sys
import os
import requests
# Add backend to path
sys.path.append(os.getcwd())



def test_altimeter():
    print("\n--- Testing Altimeter Connection ---")
    url = "http://localhost:4203/api/system/health"
    try:
        res = requests.get(url, timeout=2)
        print(f"Altimeter Health: {res.status_code}")
        print(res.json())
        
        # Test Projects
        proj_url = "http://localhost:4203/api/projects/"
        res = requests.get(proj_url, timeout=2)
        print(f"Altimeter Projects: {res.status_code}")
        data = res.json()
        print(f"Found {len(data)} projects.")
    except Exception as e:
        print(f"Altimeter Error: {e}")

if __name__ == "__main__":
    test_altimeter()
