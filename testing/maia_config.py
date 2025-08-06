import os
import yaml
import re

class MaiaConfig:
    _instance = None
    _env_var_pattern = re.compile(r"\$\{([^}^{]+)\}")

    def __init__(self, config_path=None):
        self.config_path = config_path or os.getenv("MAIA_TEST_CONFIG", "maia_test_config.yaml")
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file '{self.config_path}' not found.")

        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        self._config = self._expand_env_vars(raw_config)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MaiaConfig()
        return cls._instance

    def get_section(self, key: str, default=None):
        return self._config.get(key, default)

    def get_full_config(self):
        return self._config

    def _expand_env_vars(self, obj):
        """Recursively replaces ${VAR} with os.environ['VAR'] in the loaded YAML structure."""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(i) for i in obj]
        elif isinstance(obj, str):
            return self._env_var_pattern.sub(lambda match: os.environ.get(match.group(1), f"<<MISSING_ENV:{match.group(1)}>>"), obj)
        return obj
