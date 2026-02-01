from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """Base class for all Atlas agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input context and return results"""
        pass
