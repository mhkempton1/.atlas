from core.app import app
print("App initialized successfully")
for route in app.routes:
    if "email" in route.path:
        print(f"Route: {route.path}")
