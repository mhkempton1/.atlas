import re

with open("backend/api/task_routes.py", "r") as f:
    content = f.read()

content = content.replace('status=request.status,', 'status=getattr(request, "status", "open"),')

with open("backend/api/task_routes.py", "w") as f:
    f.write(content)

with open("backend/services/knowledge_service.py", "r") as f:
    content = f.read()

if "def get_all_documents(self)" not in content:
    content = content.replace('class KnowledgeService:', 'class KnowledgeService:\n    def get_all_documents(self):\n        return self.list_documents()\n')

with open("backend/services/knowledge_service.py", "w") as f:
    f.write(content)
