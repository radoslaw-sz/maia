from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseTool(ABC):
    """Base class for all tools that agents can use"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.call_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        pass

    async def execute(self, **kwargs) -> Any:
        """Execute the tool and record the call"""
        result = await self._execute(**kwargs)
        self.record_call(kwargs, result)
        return result
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the tool schema for LLM function calling"""
        pass
    
    def record_call(self, parameters: Dict[str, Any], result: Any):
        """Record a tool call for testing purposes"""
        self.call_history.append({
            "parameters": parameters,
            "result": result,
        })
    
    def get_call_count(self) -> int:
        """Get number of times this tool was called"""
        return len(self.call_history)
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last call made to this tool"""
        return self.call_history[-1] if self.call_history else None