"""Settings management for hab CLI."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from hab.config.paths import get_config_path


class Settings(BaseModel):
    """Application settings."""

    url: str | None = Field(default=None, description="Home Assistant URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    @classmethod
    def load(cls, config_dir: str | None = None) -> Settings:
        """Load settings from config file and environment.

        Environment variables take precedence over config file values.

        Args:
            config_dir: Optional custom configuration directory.

        Returns:
            Settings instance.
        """
        config_path = get_config_path(config_dir)
        data: dict[str, Any] = {}

        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        # Environment variable overrides
        if env_url := os.environ.get("HAB_URL"):
            data["url"] = env_url

        if env_timeout := os.environ.get("HAB_TIMEOUT"):
            try:
                data["timeout"] = int(env_timeout)
            except ValueError:
                pass

        if env_verify_ssl := os.environ.get("HAB_VERIFY_SSL"):
            data["verify_ssl"] = env_verify_ssl.lower() not in ("0", "false", "no")

        return cls(**data)

    def save(self, config_dir: str | None = None) -> None:
        """Save settings to config file.

        Args:
            config_dir: Optional custom configuration directory.
        """
        config_path = get_config_path(config_dir)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(self.model_dump(), indent=2))


@lru_cache
def get_settings(config_dir: str | None = None) -> Settings:
    """Get cached settings instance.

    Args:
        config_dir: Optional custom configuration directory.

    Returns:
        Settings instance.
    """
    return Settings.load(config_dir)


def clear_settings_cache() -> None:
    """Clear the settings cache."""
    get_settings.cache_clear()
