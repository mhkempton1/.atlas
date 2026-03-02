import re

# Fix test_knowledge_routes
with open("backend/tests/api/test_knowledge_routes.py", "r") as f:
    content = f.read()

content = content.replace("KnowledgeService.get_content", "KnowledgeService.get_document_content")

with open("backend/tests/api/test_knowledge_routes.py", "w") as f:
    f.write(content)

# Fix settings error in conftest
with open("backend/tests/conftest.py", "r") as f:
    content = f.read()

content = content.replace('monkeypatch.setattr(settings, "ONEDRIVE_PATH", str(mock_path))', 'monkeypatch.setattr(settings, "ONEDRIVE_ROOT_PATH", str(mock_path))')

with open("backend/tests/conftest.py", "w") as f:
    f.write(content)
