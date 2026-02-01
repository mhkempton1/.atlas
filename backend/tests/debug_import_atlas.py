import sys
import os

# Emulate conftest logic
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

print(f"Backend dir: {backend_dir}")
print(f"Sys path: {sys.path}")

try:
    from agents.base import BaseAgent
    print("Sucessfully imported BaseAgent")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    import agents
    print(f"Agents module: {agents}")
except ImportError as e:
    print(f"ImportError: {e}")
