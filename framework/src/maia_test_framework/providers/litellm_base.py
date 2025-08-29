# maia_test_framework/providers/litellm_base.py
import time
from typing import Dict, Any, List
from litellm import completion
from maia_test_framework.core.message import AgentResponse, Message
from .base import BaseProvider
from maia_test_framework.utils.network import wait_for_service

class LiteLLMBaseProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = self.config.get("model")
        # Subclasses should set self.api_base if needed
        self.api_base = None

    def get_provider_name(self) -> str:
        return self.model

    def _prepare_messages(self, history: List[Message], system_message: str) -> List[Dict[str, str]]:
        messages_payload = []
        if system_message.strip():
            messages_payload.append({"role": "system", "content": system_message.strip()})
        
        for message in history:
            role = message.sender_type
            if role not in ["user", "system", "tool"]:
                # TODO: Assumption is that assistant becomes the user. Improve it.
                role = "user"
            messages_payload.append(
                {"role": role, "name": message.sender, "content": message.content}
            )
        
        return messages_payload

    def _get_completion_kwargs(self, messages_payload: List[Dict[str, str]]) -> Dict[str, Any]:
        """Subclasses must implement this to provide specific kwargs for litellm.completion."""
        raise NotImplementedError

    async def generate(self, history: List[Message], system_message: str = "") -> AgentResponse:
        if self.api_base:
            await wait_for_service(self.api_base)

        messages_payload = self._prepare_messages(history, system_message)
        
        try:
            kwargs = self._get_completion_kwargs(messages_payload)
            response = completion(**kwargs)
            content = response.choices[0].message.content
            raw_response_data = response.model_dump_json()
        except Exception as e:
            print(f"Error using LiteLLM: {e}")
            content = ""
            raw_response_data = {"error": str(e)}

        return AgentResponse(
            content=content,
            raw_response=raw_response_data,
            metadata={"model": self.model},
        )
