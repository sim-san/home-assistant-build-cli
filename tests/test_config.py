"""Tests for configuration module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from hab.config.paths import get_config_dir, get_config_path, get_credentials_path
from hab.config.settings import Settings, clear_settings_cache, get_settings


class TestPaths:
    """Tests for path functions."""

    def test_get_config_dir_default(self) -> None:
        """Test default config directory."""
        config_dir = get_config_dir()
        assert "home-assistant-builder" in str(config_dir)

    def test_get_config_dir_custom(self) -> None:
        """Test custom config directory."""
        custom_path = "/custom/path"
        config_dir = get_config_dir(custom_path)
        assert str(config_dir) == custom_path

    def test_get_config_path(self, temp_config_dir: Path) -> None:
        """Test config.json path."""
        config_path = get_config_path(str(temp_config_dir))
        assert config_path == temp_config_dir / "config.json"

    def test_get_credentials_path(self, temp_config_dir: Path) -> None:
        """Test credentials.json path."""
        creds_path = get_credentials_path(str(temp_config_dir))
        assert creds_path == temp_config_dir / "credentials.json"


class TestSettings:
    """Tests for Settings class."""

    def test_settings_defaults(self) -> None:
        """Test default settings values."""
        settings = Settings()
        assert settings.url is None
        assert settings.timeout == 30
        assert settings.verify_ssl is True

    def test_settings_from_values(self) -> None:
        """Test settings with provided values."""
        settings = Settings(
            url="http://localhost:8123",
            timeout=60,
            verify_ssl=False,
        )
        assert settings.url == "http://localhost:8123"
        assert settings.timeout == 60
        assert settings.verify_ssl is False

    def test_settings_load_from_file(self, temp_config_dir: Path) -> None:
        """Test loading settings from config file."""
        config_path = temp_config_dir / "config.json"
        config_path.write_text(json.dumps({
            "url": "http://test.local:8123",
            "timeout": 45,
        }))

        settings = Settings.load(str(temp_config_dir))
        assert settings.url == "http://test.local:8123"
        assert settings.timeout == 45

    def test_settings_env_override(self, temp_config_dir: Path) -> None:
        """Test environment variables override config file."""
        config_path = temp_config_dir / "config.json"
        config_path.write_text(json.dumps({
            "url": "http://file.local:8123",
            "timeout": 45,
        }))

        with patch.dict(os.environ, {"HAB_URL": "http://env.local:8123"}):
            settings = Settings.load(str(temp_config_dir))
            assert settings.url == "http://env.local:8123"
            assert settings.timeout == 45

    def test_settings_save(self, temp_config_dir: Path) -> None:
        """Test saving settings."""
        settings = Settings(url="http://test.local:8123", timeout=60)
        settings.save(str(temp_config_dir))

        config_path = temp_config_dir / "config.json"
        assert config_path.exists()

        saved = json.loads(config_path.read_text())
        assert saved["url"] == "http://test.local:8123"
        assert saved["timeout"] == 60

    def test_get_settings_cached(self, temp_config_dir: Path) -> None:
        """Test settings caching."""
        clear_settings_cache()

        config_path = temp_config_dir / "config.json"
        config_path.write_text(json.dumps({"url": "http://cached.local:8123"}))

        settings1 = get_settings(str(temp_config_dir))
        settings2 = get_settings(str(temp_config_dir))

        assert settings1 is settings2
        clear_settings_cache()
