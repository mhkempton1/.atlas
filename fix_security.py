import re

with open("backend/tests/core/test_security.py", "r") as f:
    content = f.read()

if 'import pytest' not in content:
    content = 'import pytest\n' + content

with open("backend/tests/core/test_security.py", "w") as f:
    f.write(content)
