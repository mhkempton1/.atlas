import requests
import json

url = "http://localhost:4201/api/v1/tasks/create"
payload = {
    "title": "Diagnostic Task from Python",
    "project_id": "ATLAS-TEST",
    "priority": "high",
    "due_date": "2026-02-05T12:00:00"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
