import re

with open("backend/tests/test_sync.py", "r") as f:
    content = f.read()

content = content.replace('@pytest.mark.asyncio\n', 'import pytest\n@pytest.mark.asyncio\n')

with open("backend/tests/test_sync.py", "w") as f:
    f.write(content)
