"""Tests for basic CLI functionality."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from hab.cli.main import cli


class TestCliBasic:
    """Tests for basic CLI commands."""

    def test_version(self, cli_runner: CliRunner) -> None:
        """Test --version flag."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "hab" in result.output

    def test_help(self, cli_runner: CliRunner) -> None:
        """Test --help flag."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Home Assistant Builder" in result.output
        assert "auth" in result.output
        assert "automation" in result.output
        assert "entity" in result.output

    def test_command_group_help(self, cli_runner: CliRunner) -> None:
        """Test command group help."""
        result = cli_runner.invoke(cli, ["automation", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "get" in result.output
        assert "create" in result.output


class TestAuthCommands:
    """Tests for auth commands."""

    def test_auth_status_not_authenticated(
        self,
        cli_runner: CliRunner,
        temp_config_dir: Path,
    ) -> None:
        """Test auth status when not authenticated."""
        result = cli_runner.invoke(
            cli,
            ["--config", str(temp_config_dir), "auth", "status"],
        )
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["data"]["authenticated"] is False

    def test_auth_logout_no_credentials(
        self,
        cli_runner: CliRunner,
        temp_config_dir: Path,
    ) -> None:
        """Test logout when no credentials exist."""
        result = cli_runner.invoke(
            cli,
            ["--config", str(temp_config_dir), "auth", "logout"],
        )
        assert result.exit_code == 0

    @patch("hab.client.RestClient")
    def test_auth_login_token(
        self,
        mock_rest_client: MagicMock,
        cli_runner: CliRunner,
        temp_config_dir: Path,
    ) -> None:
        """Test login with token."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get_config = AsyncMock(return_value={
            "location_name": "Test Home",
            "version": "2024.1.0",
        })
        mock_rest_client.return_value = mock_client

        result = cli_runner.invoke(
            cli,
            [
                "--config", str(temp_config_dir),
                "auth", "login", "--token",
                "--url", "http://localhost:8123",
                "--access-token", "test_token",
            ],
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True


class TestEntityCommands:
    """Tests for entity commands."""

    @patch("hab.cli.main.Context.get_ws_client")
    def test_entity_list(
        self,
        mock_get_ws_client: MagicMock,
        cli_runner: CliRunner,
        temp_config_dir: Path,
        mock_ws_client: MagicMock,
        sample_states: list,
    ) -> None:
        """Test entity list command."""
        mock_ws_client.get_states = AsyncMock(return_value=sample_states)
        mock_ws_client.entity_registry_list = AsyncMock(return_value=[])
        mock_get_ws_client.return_value = mock_ws_client

        with patch("hab.cli.main.Context.auth") as mock_auth:
            mock_auth.is_authenticated = True
            mock_auth.url = "http://localhost:8123"
            mock_auth.token = "test_token"

            result = cli_runner.invoke(
                cli,
                ["--config", str(temp_config_dir), "entity", "list"],
            )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True
        assert len(output["data"]) == 3

    @patch("hab.cli.main.Context.get_ws_client")
    def test_entity_list_domain_filter(
        self,
        mock_get_ws_client: MagicMock,
        cli_runner: CliRunner,
        temp_config_dir: Path,
        mock_ws_client: MagicMock,
        sample_states: list,
    ) -> None:
        """Test entity list with domain filter."""
        mock_ws_client.get_states = AsyncMock(return_value=sample_states)
        mock_ws_client.entity_registry_list = AsyncMock(return_value=[])
        mock_get_ws_client.return_value = mock_ws_client

        with patch("hab.cli.main.Context.auth") as mock_auth:
            mock_auth.is_authenticated = True
            mock_auth.url = "http://localhost:8123"
            mock_auth.token = "test_token"

            result = cli_runner.invoke(
                cli,
                ["--config", str(temp_config_dir), "entity", "list", "--domain", "light"],
            )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert len(output["data"]) == 1
        assert output["data"][0]["entity_id"] == "light.living_room"


class TestAreaCommands:
    """Tests for area commands."""

    @patch("hab.cli.main.Context.get_ws_client")
    def test_area_list(
        self,
        mock_get_ws_client: MagicMock,
        cli_runner: CliRunner,
        temp_config_dir: Path,
        mock_ws_client: MagicMock,
    ) -> None:
        """Test area list command."""
        mock_ws_client.area_registry_list = AsyncMock(return_value=[
            {"area_id": "living_room", "name": "Living Room"},
            {"area_id": "bedroom", "name": "Bedroom"},
        ])
        mock_get_ws_client.return_value = mock_ws_client

        with patch("hab.cli.main.Context.auth") as mock_auth:
            mock_auth.is_authenticated = True
            mock_auth.url = "http://localhost:8123"
            mock_auth.token = "test_token"

            result = cli_runner.invoke(
                cli,
                ["--config", str(temp_config_dir), "area", "list"],
            )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True
        assert len(output["data"]) == 2

    @patch("hab.cli.main.Context.get_ws_client")
    def test_area_create(
        self,
        mock_get_ws_client: MagicMock,
        cli_runner: CliRunner,
        temp_config_dir: Path,
        mock_ws_client: MagicMock,
    ) -> None:
        """Test area create command."""
        mock_ws_client.area_registry_create = AsyncMock(return_value={
            "area_id": "kitchen",
            "name": "Kitchen",
        })
        mock_get_ws_client.return_value = mock_ws_client

        with patch("hab.cli.main.Context.auth") as mock_auth:
            mock_auth.is_authenticated = True
            mock_auth.url = "http://localhost:8123"
            mock_auth.token = "test_token"

            result = cli_runner.invoke(
                cli,
                ["--config", str(temp_config_dir), "area", "create", "Kitchen"],
            )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True


class TestTextOutput:
    """Tests for text output mode."""

    @patch("hab.cli.main.Context.get_ws_client")
    def test_text_mode(
        self,
        mock_get_ws_client: MagicMock,
        cli_runner: CliRunner,
        temp_config_dir: Path,
        mock_ws_client: MagicMock,
    ) -> None:
        """Test --text flag for human-readable output."""
        mock_ws_client.area_registry_list = AsyncMock(return_value=[
            {"area_id": "living_room", "name": "Living Room"},
        ])
        mock_get_ws_client.return_value = mock_ws_client

        with patch("hab.cli.main.Context.auth") as mock_auth:
            mock_auth.is_authenticated = True
            mock_auth.url = "http://localhost:8123"
            mock_auth.token = "test_token"

            result = cli_runner.invoke(
                cli,
                ["--config", str(temp_config_dir), "--text", "area", "list"],
            )

        assert result.exit_code == 0
        # Text mode should not produce valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.output)
