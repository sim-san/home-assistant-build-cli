"""Tests for REST client."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock

from hab.client.rest import RestClient
from hab.exceptions import (
    AuthenticationError,
    ConnectionError,
    ResourceNotFoundError,
    ValidationError,
)


class TestRestClient:
    """Tests for RestClient."""

    @pytest.fixture
    def client(self) -> RestClient:
        """Create a test client."""
        return RestClient(
            url="http://localhost:8123",
            token="test_token",
            timeout=30,
        )

    @pytest.mark.asyncio
    async def test_get_config(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test getting configuration."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/config",
            json={"location_name": "Test Home", "version": "2024.1.0"},
        )

        async with client:
            config = await client.get_config()

        assert config["location_name"] == "Test Home"
        assert config["version"] == "2024.1.0"

    @pytest.mark.asyncio
    async def test_get_states(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test getting all states."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/states",
            json=[
                {"entity_id": "light.test", "state": "on"},
                {"entity_id": "switch.test", "state": "off"},
            ],
        )

        async with client:
            states = await client.get_states()

        assert len(states) == 2
        assert states[0]["entity_id"] == "light.test"

    @pytest.mark.asyncio
    async def test_get_state(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test getting single entity state."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/states/light.test",
            json={"entity_id": "light.test", "state": "on"},
        )

        async with client:
            state = await client.get_state("light.test")

        assert state["entity_id"] == "light.test"
        assert state["state"] == "on"

    @pytest.mark.asyncio
    async def test_call_service(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test calling a service."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/services/light/turn_on",
            json=[{"entity_id": "light.test", "state": "on"}],
        )

        async with client:
            result = await client.call_service(
                "light", "turn_on", {"entity_id": "light.test"}
            )

        assert result[0]["entity_id"] == "light.test"

    @pytest.mark.asyncio
    async def test_auth_error(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test authentication error handling."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/config",
            status_code=401,
            json={"message": "Invalid token"},
        )

        async with client:
            with pytest.raises(AuthenticationError):
                await client.get_config()

    @pytest.mark.asyncio
    async def test_not_found_error(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test not found error handling."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/states/light.nonexistent",
            status_code=404,
            json={"message": "Entity not found"},
        )

        async with client:
            with pytest.raises(ResourceNotFoundError):
                await client.get_state("light.nonexistent")

    @pytest.mark.asyncio
    async def test_validation_error(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test validation error handling."""
        httpx_mock.add_response(
            url="http://localhost:8123/api/services/light/turn_on",
            status_code=400,
            json={"message": "Invalid service data"},
        )

        async with client:
            with pytest.raises(ValidationError):
                await client.call_service("light", "turn_on", {"invalid": "data"})

    @pytest.mark.asyncio
    async def test_authorization_header(self, client: RestClient, httpx_mock: HTTPXMock) -> None:
        """Test that authorization header is set."""
        httpx_mock.add_response(url="http://localhost:8123/api/config", json={})

        async with client:
            await client.get_config()

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "Bearer test_token"
