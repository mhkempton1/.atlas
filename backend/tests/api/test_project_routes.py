import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from database.models import Task

def test_get_project_context_success(client, db, monkeypatch):
    # 1. Mock Altimeter Service
    mock_altimeter = MagicMock()
    mock_altimeter.get_project_details.return_value = {
        "altimeter_project_id": "25-0308",
        "name": "Wicklow Apartments",
        "status": "In Progress",
        "percent_complete": 65,
        "project_manager_id": 101,
        "foreman_id": 102
    }

    # Mock execute_read_only_query for PM and Foreman
    def mock_query(query):
        if "id = 101" in query:
            return [{"first_name": "John", "last_name": "Smith"}]
        if "id = 102" in query:
             return [{"first_name": "Mike", "last_name": "Jones"}]
        return []

    mock_altimeter.execute_read_only_query.side_effect = mock_query

    monkeypatch.setattr("api.project_routes.altimeter_service", mock_altimeter)

    # 2. Add local tasks
    task1 = Task(title="Task 1", project_id="25-0308", status="open", priority="urgent")
    task2 = Task(title="Task 2", project_id="25-0308", status="in_progress", priority="high")
    task3 = Task(title="Task 3", project_id="25-0308", status="open", priority="medium")
    task4 = Task(title="Task 4", project_id="OTHER", status="open", priority="urgent") # Should be ignored
    task5 = Task(title="Task 5", project_id="25-0308", status="done", priority="urgent") # Should be ignored

    db.add_all([task1, task2, task3, task4, task5])
    db.commit()

    # 3. Call Endpoint
    response = client.get("/api/v1/projects/25-0308/context")

    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == "25-0308"
    assert data["name"] == "Wicklow Apartments"
    assert data["status"] == "In Progress"
    assert data["pm"] == "John Smith"
    assert data["foreman"] == "Mike Jones"

    # Check stats
    # Urgent -> critical
    # Task 1 (urgent) -> critical
    # Task 2 (high) -> high
    # Task 3 (medium) -> medium
    # Task 4 is other project
    # Task 5 is done

    assert data["tasks"]["critical"] == 1
    assert data["tasks"]["high"] == 1
    assert data["tasks"]["medium"] == 1
    assert data["tasks"]["low"] == 0

def test_get_project_context_not_found_in_altimeter(client, db, monkeypatch):
    # Mock Altimeter Service returning None
    mock_altimeter = MagicMock()
    mock_altimeter.get_project_details.return_value = None
    monkeypatch.setattr("api.project_routes.altimeter_service", mock_altimeter)

    # Add a task just to verify it still counts
    task1 = Task(title="Task 1", project_id="UNKNOWN-1", status="open", priority="high")
    db.add(task1)
    db.commit()

    response = client.get("/api/v1/projects/UNKNOWN-1/context")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Unknown Project"
    assert data["tasks"]["high"] == 1
