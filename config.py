from typing import Dict, Optional

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    # Application logging (src directory)
    APP_LOG_LEVEL: str = Field(default="INFO", description="Application logging level")

    # Dependencies logging (all other libraries)
    DEPS_LOG_LEVEL: str = Field(default="WARNING", description="Dependencies logging level")

    # Specific logger levels - can be used to override levels for specific loggers
    LOGGER_OVERRIDES: Dict[str, str] = Field(
        default_factory=lambda: {
            "uvicorn": "WARNING",
            "fastapi": "WARNING",
            "motor": "WARNING",
        },
        description="Override log levels for specific libraries",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class Config(
    LoggingSettings,
):
    """Global application settings."""

    APP_NAME: str = Field(default="AI Test Framework", description="Application name")

    # Keep for backward compatibility
    LOG_LEVEL: str = Field(
        default="INFO", description="Legacy logging level (use APP_LOG_LEVEL instead)"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )
config = Config()
