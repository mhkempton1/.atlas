import re

with open("backend/tests/test_sync_integration.py", "r") as f:
    content = f.read()

if 'import pytest' not in content:
    content = 'import pytest\n' + content

with open("backend/tests/test_sync_integration.py", "w") as f:
    f.write(content)
