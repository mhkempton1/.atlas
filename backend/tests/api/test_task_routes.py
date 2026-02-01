import pytest

def test_create_task(client):
    response = client.post("/api/v1/tasks/create", json={
        "title": "Fix electrical panel",
        "priority": "high",
        "category": "work"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Fix electrical panel"
    assert data["status"] == "todo"

def test_get_tasks(client, db):
    from database.models import Task
    task = Task(title="Test Task", status="todo", priority="medium", created_from="manual")
    db.add(task)
    db.commit()

    response = client.get("/api/v1/tasks/list")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_update_task_status(client, db):
    from database.models import Task
    task = Task(title="Update Me", status="todo", priority="low", created_from="manual")
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.put(f"/api/v1/tasks/{task.task_id}", json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"

def test_delete_task(client, db):
    from database.models import Task
    task = Task(title="Delete Me", status="todo", priority="low", created_from="manual")
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.delete(f"/api/v1/tasks/{task.task_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_update_nonexistent_task(client):
    response = client.put("/api/v1/tasks/99999", json={"status": "done"})
    assert response.status_code == 404

def test_delete_nonexistent_task(client):
    response = client.delete("/api/v1/tasks/99999")
    assert response.status_code == 404

def test_filter_tasks_by_status(client, db):
    from database.models import Task
    db.add(Task(title="Active", status="in_progress", priority="high", created_from="manual"))
    db.add(Task(title="Done", status="done", priority="low", created_from="manual"))
    db.commit()

    response = client.get("/api/v1/tasks/list?status=in_progress")
    assert response.status_code == 200
    for task in response.json():
        assert task["status"] == "in_progress"
