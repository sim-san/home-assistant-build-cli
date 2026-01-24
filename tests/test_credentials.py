"""Tests for credentials module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from hab.auth.credentials import (
    Credentials,
    delete_credentials,
    load_credentials,
    save_credentials,
)


class TestCredentials:
    """Tests for Credentials class."""

    def test_credentials_token(self) -> None:
        """Test token-based credentials."""
        creds = Credentials(
            url="http://localhost:8123",
            access_token="my_token",
        )
        assert creds.url == "http://localhost:8123"
        assert creds.access_token == "my_token"
        assert creds.is_oauth is False
        assert creds.has_valid_token is True

    def test_credentials_oauth(self) -> None:
        """Test OAuth credentials."""
        creds = Credentials(
            url="http://localhost:8123",
            access_token="access_token",
            refresh_token="refresh_token",
            token_expiry=1234567890.0,
        )
        assert creds.is_oauth is True
        assert creds.has_valid_token is True

    def test_credentials_no_token(self) -> None:
        """Test credentials without token."""
        creds = Credentials(url="http://localhost:8123")
        assert creds.has_valid_token is False


class TestCredentialStorage:
    """Tests for credential storage functions."""

    def test_save_and_load_credentials(self, temp_config_dir: Path) -> None:
        """Test saving and loading credentials."""
        creds = Credentials(
            url="http://localhost:8123",
            access_token="test_token",
        )

        save_credentials(creds, str(temp_config_dir))

        # Verify file exists and has restrictive permissions
        creds_path = temp_config_dir / "credentials.json"
        assert creds_path.exists()
        assert (creds_path.stat().st_mode & 0o777) == 0o600

        # Load and verify
        loaded = load_credentials(str(temp_config_dir))
        assert loaded is not None
        assert loaded.url == "http://localhost:8123"
        assert loaded.access_token == "test_token"

    def test_load_credentials_not_found(self, temp_config_dir: Path) -> None:
        """Test loading when no credentials exist."""
        loaded = load_credentials(str(temp_config_dir))
        assert loaded is None

    def test_load_credentials_from_env(self, temp_config_dir: Path) -> None:
        """Test loading credentials from environment."""
        with patch.dict(os.environ, {
            "HAB_URL": "http://env.local:8123",
            "HAB_TOKEN": "env_token",
        }):
            loaded = load_credentials(str(temp_config_dir))
            assert loaded is not None
            assert loaded.url == "http://env.local:8123"
            assert loaded.access_token == "env_token"

    def test_delete_credentials(self, temp_config_dir: Path) -> None:
        """Test deleting credentials."""
        creds = Credentials(url="http://localhost:8123", access_token="test")
        save_credentials(creds, str(temp_config_dir))

        result = delete_credentials(str(temp_config_dir))
        assert result is True

        creds_path = temp_config_dir / "credentials.json"
        assert not creds_path.exists()

    def test_delete_credentials_not_found(self, temp_config_dir: Path) -> None:
        """Test deleting when no credentials exist."""
        result = delete_credentials(str(temp_config_dir))
        assert result is False
