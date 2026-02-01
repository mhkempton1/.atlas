import pytest
import os
from services.knowledge_service import KnowledgeService

@pytest.fixture
def knowledge_service_instance(temp_onedrive):
    return KnowledgeService()

def test_scan_directory_logic(knowledge_service_instance, temp_onedrive):
    # Create a test file in GUIDELINES
    path = temp_onedrive / "GUIDELINES" / "test.md"
    with open(path, 'w', encoding='utf-8') as f:
        f.write("# Test Title\nContent")
        
    docs = knowledge_service_instance.get_all_documents()
    assert len(docs) > 0
    test_doc = next(d for d in docs if d["filename"] == "test.md")
    assert test_doc["title"] == "Test Title"
    assert test_doc["source"] == "OneDrive/GUIDELINES"

def test_get_document_content(knowledge_service_instance, temp_onedrive):
    path = temp_onedrive / "GUIDELINES" / "content.md"
    with open(path, 'w', encoding='utf-8') as f:
        f.write("Full Content Here")
        
    content = knowledge_service_instance.get_document_content(str(path))
    assert content == "Full Content Here"
