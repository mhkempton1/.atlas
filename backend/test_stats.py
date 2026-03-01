from fastapi.testclient import TestClient
from core.app import app
import traceback

client = TestClient(app)
try:
    response = client.get("/api/v1/dashboard/stats")
    print("STATUS:", response.status_code)
    print("DATA:", response.text)
except Exception as e:
    with open("out.txt", "w") as f:
        traceback.print_exc(file=f)
