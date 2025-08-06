# framework/testing/config.py
import os
import re
import yaml
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

@dataclass
class ProviderConfig:
    """Configuration for a specific provider"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    timeout: int = 30
    
    def is_available(self) -> bool:
        """Check if provider has required credentials/configuration"""
        if self.api_key is None and self.base_url is None:
            return False
        return True
    
    def merge_with(self, override_config: Dict[str, Any]) -> 'ProviderConfig':
        """Create new config with overrides applied"""
        config_dict = {
            'api_key': self.api_key,
            'base_url': self.base_url,
            'default_model': self.default_model,
            'timeout': self.timeout,
        }
        config_dict.update(override_config)
        return ProviderConfig(**config_dict)

class TestConfig:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = self._resolve_config_path(config_path)
        self.config_data = self._load_config()
        self._substitute_env_vars()
        self._providers = self._parse_providers()
    
    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve configuration file path with multiple fallback options"""
        if config_path:
            return Path(config_path)
        
        # Check environment variable
        env_path = os.getenv("MAIA_TEST_CONFIG")
        if env_path:
            return Path(env_path)
        
        # Check common locations
        possible_paths = [
            Path("config.yaml"),
            Path("config/config.yaml"),
            Path("tests/config/config.yaml"),
            Path.home() / ".maia" / "config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError(
            f"Test config not found. Tried: {[str(p) for p in possible_paths]}. "
            f"Set MAIA_TEST_CONFIG environment variable or provide config_path."
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to load config from {self.config_path}: {e}")
    
    def _substitute_env_vars(self):
        """Replace ${VAR} and ${VAR:default} patterns with environment values"""
        def substitute_value(value):
            if isinstance(value, str):
                # Pattern: ${VAR} or ${VAR:default}
                pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
                
                def replace_match(match):
                    var_name = match.group(1)
                    default_value = match.group(2) if match.group(2) is not None else None
                    env_value = os.getenv(var_name, default_value)
                    
                    if env_value is None:
                        raise ValueError(f"Environment variable {var_name} not set and no default provided")
                    
                    # Convert string booleans to actual booleans
                    if env_value.lower() in ('true', 'false'):
                        return str(env_value.lower() == 'true')
                    
                    return env_value
                
                return re.sub(pattern, replace_match, value)
            
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            
            return value
        
        self.config_data = substitute_value(self.config_data)
    
    def _parse_providers(self) -> Dict[str, ProviderConfig]:
        """Parse provider configurations"""
        providers = {}
        provider_configs = self.config_data.get('providers', {})
        
        for name, config in provider_configs.items():
            providers[name] = ProviderConfig(**config)
        
        return providers
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        return self._providers.get(provider_name)
    
    def has_provider(self, provider_name: str) -> bool:
        """Check if provider is configured and available"""
        provider_config = self.get_provider_config(provider_name)
        return provider_config is not None and provider_config.is_available()
    
    def get_available_providers(self) -> List[str]:
        """Get list of all available providers"""
        return [name for name, config in self._providers.items() if config.is_available()]
    
    def get_test_settings(self) -> Dict[str, Any]:
        """Get general test settings"""
        return self.config_data.get('test_settings', {})
    
    def create_provider_config(self, provider_name: str, overrides: Dict[str, Any] = None) -> ProviderConfig:
        """Create provider config with optional overrides"""
        base_config = self.get_provider_config(provider_name)
        if base_config is None:
            raise ValueError(f"Provider '{provider_name}' not configured")
        
        if overrides:
            return base_config.merge_with(overrides)
        
        return base_config