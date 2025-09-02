from typing import Dict, Any
import asyncio
from maia_test_framework.core.tools.base import BaseTool

class WeatherAPITool(BaseTool):
    """Weather API tool for testing"""
    
    def __init__(self, name: str, api_key: str = None, mock_responses: Dict[str, Any] = None):
        super().__init__(name, "Get current weather information for a location")
        self.api_key = api_key
        self.mock_responses = mock_responses or {}
    
    async def _execute(self, location: str, **kwargs) -> Dict[str, Any]:
        """Execute weather API call"""
        if self.mock_responses:
            result = self.mock_responses.get(location.lower(), {
                "location": location,
                "temperature": 20,
                "condition": "sunny",
                "humidity": 60
            })
        else:
            result = await self._make_api_call(location)
        
        return result
    
    async def _make_api_call(self, location: str) -> Dict[str, Any]:
        """Make actual API call (placeholder)"""
        # Simulate API delay
        await asyncio.sleep(0.1)
        return {
            "location": location,
            "temperature": 22,
            "condition": "partly cloudy",
            "humidity": 65
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for LLM function calling"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or location to get weather for"
                    }
                },
                "required": ["location"]
            }
        }