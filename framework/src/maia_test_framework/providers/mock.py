from typing import Dict, Any, Callable
from maia_test_framework.core.message import AgentResponse
from maia_test_framework.providers.base import BaseProvider

class MockProvider(BaseProvider):
    """A mock provider that returns pre-configured responses or generates them dynamically."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.responses = self.config.get("responses", [])
        self.response_function: Callable[[str], str] = self.config.get("response_function")
        self.response_index = 0

    def get_provider_name(self) -> str:
        return "Mock"

    async def generate(self, history: list, system_message: str = "", ignore_trigger_prompt: str = "") -> AgentResponse:
        """Generates a response using a function or from a pre-configured list."""
        user_prompt = history[-1].content if history else ""

        if self.response_function:
            response_content = self.response_function(user_prompt)
            return AgentResponse(content=response_content)
        elif self.response_index < len(self.responses):
            response_content = self.responses[self.response_index]
            self.response_index += 1
            return AgentResponse(content=response_content)
        else:
            return AgentResponse(content="")
