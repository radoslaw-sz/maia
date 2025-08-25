from typing import Dict, Any, List
from .litellm_base import LiteLLMBaseProvider

class GenericLiteLLMProvider(LiteLLMBaseProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = self.config.get("api_base")

    def get_provider_name(self) -> str:
        return "GenericLiteLLM"

    def _get_completion_kwargs(self, messages_payload: List[Dict[str, str]]) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages_payload,
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base
        return kwargs
