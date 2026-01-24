"""Pytest configuration and fixtures."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from hab.auth.credentials import Credentials
from hab.cli.main import cli


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_credentials() -> Credentials:
    """Create mock credentials."""
    return Credentials(
        url="http://localhost:8123",
        access_token="test_token_12345",
    )


@pytest.fixture
def mock_rest_client() -> MagicMock:
    """Create a mock REST client."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.delete = AsyncMock()
    client.get_config = AsyncMock(return_value={
        "location_name": "Test Home",
        "version": "2024.1.0",
    })
    client.get_states = AsyncMock(return_value=[])
    client.get_services = AsyncMock(return_value=[])
    client.call_service = AsyncMock()
    return client


@pytest.fixture
def mock_ws_client() -> MagicMock:
    """Create a mock WebSocket client."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.send_command = AsyncMock()
    client.get_states = AsyncMock(return_value=[])
    client.get_config = AsyncMock(return_value={})
    client.area_registry_list = AsyncMock(return_value=[])
    client.floor_registry_list = AsyncMock(return_value=[])
    client.label_registry_list = AsyncMock(return_value=[])
    client.device_registry_list = AsyncMock(return_value=[])
    client.entity_registry_list = AsyncMock(return_value=[])
    return client


@pytest.fixture
def env_credentials(temp_config_dir: Path) -> Generator[dict[str, str], None, None]:
    """Set up environment variables for credentials."""
    env = {
        "HAB_URL": "http://localhost:8123",
        "HAB_TOKEN": "test_env_token",
        "HAB_CONFIG_DIR": str(temp_config_dir),
    }
    with patch.dict(os.environ, env, clear=False):
        yield env


@pytest.fixture
def sample_automation_config() -> dict[str, Any]:
    """Sample automation configuration."""
    return {
        "alias": "Test Automation",
        "description": "A test automation",
        "trigger": [
            {
                "platform": "state",
                "entity_id": "light.living_room",
                "to": "on",
            }
        ],
        "action": [
            {
                "service": "notify.notify",
                "data": {"message": "Light turned on"},
            }
        ],
    }


@pytest.fixture
def sample_states() -> list[dict[str, Any]]:
    """Sample entity states."""
    return [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
            },
        },
        {
            "entity_id": "switch.kitchen",
            "state": "off",
            "attributes": {
                "friendly_name": "Kitchen Switch",
            },
        },
        {
            "entity_id": "automation.test",
            "state": "on",
            "attributes": {
                "friendly_name": "Test Automation",
                "last_triggered": "2024-01-15T10:30:00Z",
            },
        },
    ]
