from typing import Dict, Any, List
from .litellm_base import LiteLLMBaseProvider

class OllamaProvider(LiteLLMBaseProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = self.config.get("host")
        self.model = f"ollama/{self.config.get('model', 'mistral')}"

    def get_provider_name(self) -> str:
        return "Ollama"

    def _get_completion_kwargs(self, messages_payload: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages_payload,
            "api_base": self.api_base
        }
