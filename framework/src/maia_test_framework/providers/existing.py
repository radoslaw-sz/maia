import asyncio
import time
from typing import Any, Dict, List
from maia_test_framework.core.message import AgentResponse, Message
from maia_test_framework.providers.base import BaseProvider


class ExistingAgentProvider(BaseProvider):
    """Provider for existing agent implementations (CrewAI, AutoGen, custom)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agent_instance = config.get('agent_instance')
        self.call_method = config.get('call_method', 'run')
        self.response_extractor = config.get('response_extractor', lambda x: str(x))

    def get_provider_name(self) -> str:
        return "Existing"
    
    async def generate(self, history: List[Message], system_message: str = "", ignore_trigger_prompt: str = "") -> AgentResponse:
        start_time = time.time()
        user_prompt = history[-1].content if history else ""
        
        try:
            # Call the existing agent however it needs to be called
            if hasattr(self.agent_instance, self.call_method):
                method = getattr(self.agent_instance, self.call_method)
                if asyncio.iscoroutinefunction(method):
                    raw_response = await method(user_prompt)
                else:
                    raw_response = method(user_prompt)
            else:
                # Try to call the agent directly
                if callable(self.agent_instance):
                    raw_response = self.agent_instance(user_prompt)
                else:
                    raise ValueError(f"Don't know how to call agent: {self.agent_instance}")
            
            processing_time = time.time() - start_time
            
            # Extract content using the provided extractor function
            content = self.response_extractor(raw_response)
            
            return AgentResponse(
                content=content,
                metadata={"agent_type": "existing"},
                processing_time=processing_time,
                raw_response=raw_response,
            )
            
        except Exception as e:
            return AgentResponse(
                content="",
                metadata={"error": True, "error_message": str(e)},
                processing_time=time.time() - start_time,
            )