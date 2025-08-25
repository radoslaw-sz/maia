from maia_test_framework.testing.maia_config import MaiaConfig
from maia_test_framework.providers.ollama import OllamaProvider
from maia_test_framework.providers.generic_lite_llm import GenericLiteLLMProvider

PROVIDER_CLASSES = {
    "OllamaProvider": OllamaProvider,
    "GenericLiteLLMProvider": GenericLiteLLMProvider,
}

class ProviderMixin:
    _provider_registry = None

    def _load_provider_registry(self):
        if self._provider_registry is not None:
            return self._provider_registry

        config = MaiaConfig.get_instance()
        raw_providers = config.get_section("providers", {})

        providers = {}
        for name, entry in raw_providers.items():
            cls_name = entry.get("class")
            provider_cls = PROVIDER_CLASSES.get(cls_name)
            if not provider_cls:
                raise ValueError(f"Unknown provider class '{cls_name}' for provider '{name}'")

            providers[name] = provider_cls(config=entry.get("config", {}))

        self._provider_registry = providers
        return providers

    def get_provider(self, name: str):
        if self._provider_registry is None:
            self._load_provider_registry()
        provider = self._provider_registry.get(name)
        if not provider:
            raise ValueError(f"Provider '{name}' not found.")
        return provider
