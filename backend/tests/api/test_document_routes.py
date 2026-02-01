import pytest
import os

def test_list_documents_empty(client, temp_onedrive):
    response = client.get("/api/v1/docs/list")
    assert response.status_code == 200
    data = response.json()
    assert data["draft"] == []
    assert data["review"] == []
    assert data["locked"] == []

def test_create_and_get_draft(client, temp_onedrive):
    # Create draft
    response = client.post("/api/v1/docs/draft/create", json={
        "title": "API Test",
        "content": "API Content"
    })
    assert response.status_code == 200
    path = response.json()["path"]
    
    # Get content
    response = client.get(f"/api/v1/docs/content?path={path}")
    assert response.status_code == 200
    assert "API Content" in response.json()["content"]

def test_save_draft(client, temp_onedrive):
    # Create first
    res_create = client.post("/api/v1/docs/draft/create", json={
        "title": "Save Test",
        "content": "Old"
    })
    path = res_create.json()["path"]
    
    # Save new content
    response = client.post("/api/v1/docs/draft/save", json={
        "path": path,
        "content": "New Content"
    })
    assert response.status_code == 200
    
    # Verify
    res_get = client.get(f"/api/v1/docs/content?path={path}")
    assert "New Content" in res_get.json()["content"]

def test_delete_draft(client, temp_onedrive):
    res_create = client.post("/api/v1/docs/draft/create", json={"title": "Delete", "content": "X"})
    path = res_create.json()["path"]
    
    response = client.delete(f"/api/v1/docs/draft?path={path}")
    assert response.status_code == 200
    assert not os.path.exists(path)

def test_promotion_workflow_api(client, temp_onedrive):
    # Create draft
    res_create = client.post("/api/v1/docs/draft/create", json={"title": "Promo", "content": "X"})
    draft_path = res_create.json()["path"]
    
    # Promote
    response = client.post("/api/v1/docs/promo/promote", json={"path": draft_path})
    # Wait, the prefix is /docs in api/routes.py, and then it includes doc_router.
    # In api/routes.py: router.include_router(doc_router, prefix="/docs", tags=["Document Control"])
    # So the full path is /api/v1/docs/promote.
    
    # Let's check api/routes.py again.
    # @router.post("/promote") in document_control_routes.py
    # prefixed with /docs in routes.py
    # prefixed with /api/v1 in main.py
    
    response = client.post("/api/v1/docs/promote", json={"path": draft_path})
    assert response.status_code == 200
    review_path = response.json()["new_path"]
    assert "REVIEW" in review_path
    
    # Lock
    response = client.post("/api/v1/docs/lock", json={"path": review_path, "approver": "API Admin"})
    assert response.status_code == 200
    locked_path = response.json()["new_path"]
    assert "LOCKED" in locked_path
    assert not os.path.exists(review_path)
