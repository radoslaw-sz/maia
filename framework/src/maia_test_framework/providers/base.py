# maia_test_framework/providers/base.py
import time
from abc import ABC, abstractmethod
from typing import Dict, List
from maia_test_framework.core.message import Message, AgentResponse, TimedAgentResponse

class BaseProvider(ABC):
    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    async def generate(self, history: List[Message], system_message: str = "") -> AgentResponse:
        pass

    async def base_generate(self, history: List[Message], system_message: str = "", ignore_trigger_prompt: str = "") -> TimedAgentResponse:
        system_message = self.handle_ignore_trigger_prompt(system_message, ignore_trigger_prompt)
        
        start_time = time.time()
        agent_response = await self.generate(history, system_message)
        processing_time = time.time() - start_time
        
        return TimedAgentResponse(
            content=agent_response.content,
            metadata=agent_response.metadata,
            raw_response=agent_response.raw_response,
            processing_time=processing_time,
        )

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    def handle_ignore_trigger_prompt(self, system_message: str, ignore_trigger_prompt: str) -> str:
        if ignore_trigger_prompt:
            return f"{system_message}\n\n{ignore_trigger_prompt}"
        return system_message
