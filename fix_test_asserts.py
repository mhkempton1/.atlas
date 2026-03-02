import re

with open("backend/tests/api/test_task_routes.py", "r") as f:
    content = f.read()

content = content.replace('assert data["status"] == "todo"', 'assert data["status"] == "open"')

with open("backend/tests/api/test_task_routes.py", "w") as f:
    f.write(content)

with open("backend/tests/api/test_knowledge_routes.py", "r") as f:
    content = f.read()

content = content.replace('KnowledgeService.get_document_content', 'KnowledgeService.get_content')

with open("backend/tests/api/test_knowledge_routes.py", "w") as f:
    f.write(content)
