import pytest
import os
from services.document_control_service import DocumentControlService

@pytest.fixture
def doc_service(temp_onedrive):
    service = DocumentControlService()
    service.root_path = str(temp_onedrive)
    return service

def test_versioning_logic(doc_service):
    assert doc_service._increment_version("1.0") == "1.1"
    assert doc_service._increment_version("1.9") == "1.10"
    assert doc_service._increment_version("v1.0") == "1.1" # Error fallback

def test_create_draft_success(doc_service):
    result = doc_service.create_draft("Test Document", "Content here")
    assert result["status"] == "created"
    assert os.path.exists(result["path"])
    
    with open(result["path"], 'r') as f:
        content = f.read()
        assert "document_state: DRAFT" in content
        assert "# Test Document" in content

def test_create_draft_duplicate(doc_service):
    doc_service.create_draft("Duplicate", "Content")
    with pytest.raises(FileExistsError):
        doc_service.create_draft("Duplicate", "Content")

def test_promote_to_review(doc_service):
    draft = doc_service.create_draft("Plan", "Initial Plan")
    draft_path = draft["path"]
    
    result = doc_service.promote_to_review(draft_path)
    assert result["status"] == "success"
    assert "REVIEW-v1.0.md" in result["new_path"]
    assert os.path.exists(result["new_path"])
    
    with open(result["new_path"], 'r') as f:
        assert "document_state: REVIEW" in f.read()

def test_promote_with_existing_locked_version(doc_service):
    # Mock an existing LOCKED v1.1
    locked_dir = os.path.join(doc_service.root_path, "GUIDELINES", "LOCKED")
    os.makedirs(locked_dir, exist_ok=True)
    with open(os.path.join(locked_dir, "plan.LOCKED-v1.1.md"), 'w') as f:
        f.write("Old content")
        
    draft = doc_service.create_draft("Plan", "New Version")
    result = doc_service.promote_to_review(draft["path"])
    
    assert result["version"] == "1.2"
    assert "REVIEW-v1.2.md" in result["new_path"]

def test_lock_document_workflow(doc_service):
    # Setup review file
    draft = doc_service.create_draft("Final", "Final Content")
    review = doc_service.promote_to_review(draft["path"])
    review_path = review["new_path"]
    
    result = doc_service.lock_document(review_path, "Approver Name")
    assert result["status"] == "success"
    
    locked_path = result["new_path"]
    assert "LOCKED-v1.0.md" in locked_path
    assert not os.path.exists(review_path)
    
    with open(locked_path, 'r') as f:
        content = f.read()
        assert "document_state: LOCKED" in content
        assert "approver: Approver Name" in content

def test_lock_document_archives_old(doc_service):
    # Setup existing LOCKED
    locked_dir = os.path.join(doc_service.root_path, "GUIDELINES", "LOCKED")
    os.makedirs(locked_dir, exist_ok=True)
    old_locked = os.path.join(locked_dir, "file.LOCKED-v1.0.md")
    with open(old_locked, 'w') as f: f.write("old")
    
    # Setup new review v1.1
    # We need to manually create this or use promote with existing v1.0
    # Let's use the service to ensure consistent paths
    draft = doc_service.create_draft("File", "new content")
    review = doc_service.promote_to_review(draft["path"]) # Should be v1.1
    
    doc_service.lock_document(review["new_path"], "Boss")
    
    # Check archive
    archive_dir = os.path.join(doc_service.root_path, "GUIDELINES", "ARCHIVE")
    archives = os.listdir(archive_dir)
    assert len(archives) == 1
    assert "file.ARCHIVE-v1.0" in archives[0]
    assert not os.path.exists(old_locked)
