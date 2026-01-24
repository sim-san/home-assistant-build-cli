"""REST API client for Home Assistant."""

from __future__ import annotations

from typing import Any

import httpx

from hab.exceptions import (
    AuthenticationError,
    ConnectionError,
    ResourceNotFoundError,
    TimeoutError,
    ValidationError,
)


class RestClient:
    """HTTP client for Home Assistant REST API."""

    def __init__(
        self,
        url: str,
        token: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the REST client.

        Args:
            url: Home Assistant URL.
            token: Access token.
            timeout: Request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.base_url = url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "RestClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses.

        Args:
            response: HTTP response to check.

        Raises:
            Appropriate exception based on status code.
        """
        if response.is_success:
            return

        try:
            data = response.json()
            message = data.get("message", response.text)
        except Exception:
            message = response.text

        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {message}")
        elif response.status_code == 403:
            from hab.exceptions import PermissionError
            raise PermissionError(f"Permission denied: {message}")
        elif response.status_code == 404:
            raise ResourceNotFoundError(f"Not found: {message}")
        elif response.status_code == 400:
            raise ValidationError(f"Bad request: {message}")
        else:
            raise ConnectionError(f"API error ({response.status_code}): {message}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Make an HTTP request.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            **kwargs: Additional request arguments.

        Returns:
            Response data.

        Raises:
            Various exceptions based on response.
        """
        url = f"/api/{endpoint.lstrip('/')}"

        try:
            response = await self.client.request(method, url, **kwargs)
            self._handle_error(response)

            if response.status_code == 204:
                return None

            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()

            return response.text

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect: {e}")

    async def get(self, endpoint: str, **kwargs: Any) -> Any:
        """Make a GET request.

        Args:
            endpoint: API endpoint.
            **kwargs: Additional request arguments.

        Returns:
            Response data.
        """
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, data: Any = None, **kwargs: Any) -> Any:
        """Make a POST request.

        Args:
            endpoint: API endpoint.
            data: JSON body data.
            **kwargs: Additional request arguments.

        Returns:
            Response data.
        """
        return await self._request("POST", endpoint, json=data, **kwargs)

    async def put(self, endpoint: str, data: Any = None, **kwargs: Any) -> Any:
        """Make a PUT request.

        Args:
            endpoint: API endpoint.
            data: JSON body data.
            **kwargs: Additional request arguments.

        Returns:
            Response data.
        """
        return await self._request("PUT", endpoint, json=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> Any:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint.
            **kwargs: Additional request arguments.

        Returns:
            Response data.
        """
        return await self._request("DELETE", endpoint, **kwargs)

    # High-level API methods

    async def get_config(self) -> dict[str, Any]:
        """Get Home Assistant configuration."""
        return await self.get("config")

    async def get_states(self) -> list[dict[str, Any]]:
        """Get all entity states."""
        return await self.get("states")

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """Get state for a specific entity.

        Args:
            entity_id: Entity ID.

        Returns:
            Entity state.
        """
        return await self.get(f"states/{entity_id}")

    async def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Set state for an entity.

        Args:
            entity_id: Entity ID.
            state: New state value.
            attributes: Optional attributes.

        Returns:
            Updated entity state.
        """
        data = {"state": state}
        if attributes:
            data["attributes"] = attributes
        return await self.post(f"states/{entity_id}", data)

    async def get_services(self) -> list[dict[str, Any]]:
        """Get all available services."""
        return await self.get("services")

    async def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> Any:
        """Call a service.

        Args:
            domain: Service domain.
            service: Service name.
            data: Service data.
            return_response: Whether to return the service response.

        Returns:
            Service response if return_response is True.
        """
        if data is None:
            data = {}
        if return_response:
            data["return_response"] = True
        return await self.post(f"services/{domain}/{service}", data)

    async def get_history(
        self,
        entity_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[list[dict[str, Any]]]:
        """Get state history.

        Args:
            entity_id: Optional entity ID to filter.
            start_time: Start time (ISO format).
            end_time: End time (ISO format).

        Returns:
            History data.
        """
        params: dict[str, str] = {}
        if entity_id:
            params["filter_entity_id"] = entity_id
        if end_time:
            params["end_time"] = end_time

        endpoint = "history/period"
        if start_time:
            endpoint = f"history/period/{start_time}"

        return await self.get(endpoint, params=params)

    async def render_template(self, template: str) -> str:
        """Render a Jinja2 template.

        Args:
            template: Template string.

        Returns:
            Rendered template.
        """
        return await self.post("template", {"template": template})

    async def check_config(self) -> dict[str, Any]:
        """Check Home Assistant configuration.

        Returns:
            Configuration check result.
        """
        return await self.post("config/core/check_config")

    async def restart(self) -> None:
        """Restart Home Assistant."""
        await self.post("services/homeassistant/restart")

    async def get_error_log(self) -> str:
        """Get error log.

        Returns:
            Error log content.
        """
        return await self.get("error_log")
