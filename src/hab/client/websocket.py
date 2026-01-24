"""WebSocket client for Home Assistant."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import websockets
from websockets.asyncio.client import ClientConnection

from hab.exceptions import AuthenticationError, ConnectionError


class WebSocketClient:
    """WebSocket client for Home Assistant real-time API."""

    def __init__(
        self,
        url: str,
        token: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            url: Home Assistant URL.
            token: Access token.
            timeout: Connection timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")
        self.ws_url = f"{ws_url}/api/websocket"
        self.token = token
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self._ws: ClientConnection | None = None
        self._message_id = 0
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._subscriptions: dict[int, Callable[[dict[str, Any]], None]] = {}
        self._receive_task: asyncio.Task[None] | None = None
        self._authenticated = False

    async def connect(self) -> None:
        """Connect and authenticate to the WebSocket.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection fails.
        """
        try:
            ssl_context = None if self.verify_ssl else False
            self._ws = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                max_size=20 * 1024 * 1024,  # 20MB
                ssl=ssl_context,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket: {e}")

        # Wait for auth_required message
        message = await self._receive()
        if message.get("type") != "auth_required":
            raise AuthenticationError(f"Unexpected message: {message}")

        # Send authentication
        await self._send({"type": "auth", "access_token": self.token})

        # Wait for auth result
        message = await self._receive()
        if message.get("type") == "auth_invalid":
            raise AuthenticationError(f"Authentication failed: {message.get('message')}")
        elif message.get("type") != "auth_ok":
            raise AuthenticationError(f"Unexpected auth response: {message}")

        self._authenticated = True

        # Start receive loop
        self._receive_task = asyncio.create_task(self._receive_loop())

    async def close(self) -> None:
        """Close the WebSocket connection."""
        self._authenticated = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        # Cancel pending requests
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()
        self._subscriptions.clear()

    async def __aenter__(self) -> "WebSocketClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _next_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id

    async def _send(self, message: dict[str, Any]) -> None:
        """Send a message.

        Args:
            message: Message to send.
        """
        if not self._ws:
            raise ConnectionError("Not connected")
        await self._ws.send(json.dumps(message))

    async def _receive(self) -> dict[str, Any]:
        """Receive a message.

        Returns:
            Received message.
        """
        if not self._ws:
            raise ConnectionError("Not connected")
        data = await self._ws.recv()
        return json.loads(data)

    async def _receive_loop(self) -> None:
        """Background task for receiving messages."""
        try:
            while self._ws:
                try:
                    data = await self._ws.recv()
                    message = json.loads(data)
                    await self._handle_message(message)
                except websockets.ConnectionClosed:
                    break
                except json.JSONDecodeError:
                    continue
        except asyncio.CancelledError:
            pass

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle a received message.

        Args:
            message: Received message.
        """
        msg_id = message.get("id")

        if message.get("type") == "event":
            # Subscription event
            if msg_id in self._subscriptions:
                self._subscriptions[msg_id](message.get("event", {}))
        elif message.get("type") == "result":
            # Command result
            if msg_id in self._pending:
                future = self._pending.pop(msg_id)
                if not future.done():
                    if message.get("success"):
                        future.set_result(message.get("result"))
                    else:
                        error = message.get("error", {})
                        future.set_exception(
                            ConnectionError(error.get("message", "Unknown error"))
                        )
        elif message.get("type") == "pong":
            # Ping response
            if msg_id in self._pending:
                future = self._pending.pop(msg_id)
                if not future.done():
                    future.set_result(None)

    async def send_command(
        self,
        command_type: str,
        **kwargs: Any,
    ) -> Any:
        """Send a command and wait for response.

        Args:
            command_type: Command type.
            **kwargs: Command parameters.

        Returns:
            Command result.
        """
        msg_id = self._next_id()
        message = {"id": msg_id, "type": command_type, **kwargs}

        future: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = future

        try:
            await self._send(message)
            return await asyncio.wait_for(future, timeout=self.timeout)
        except asyncio.TimeoutError:
            self._pending.pop(msg_id, None)
            raise
        except Exception:
            self._pending.pop(msg_id, None)
            raise

    async def subscribe(
        self,
        event_type: str | None,
        callback: Callable[[dict[str, Any]], None],
    ) -> int:
        """Subscribe to events.

        Args:
            event_type: Event type to subscribe to, or None for all events.
            callback: Callback for received events.

        Returns:
            Subscription ID for unsubscribing.
        """
        msg_id = self._next_id()
        message: dict[str, Any] = {"id": msg_id, "type": "subscribe_events"}
        if event_type:
            message["event_type"] = event_type

        future: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = future
        self._subscriptions[msg_id] = callback

        await self._send(message)
        await asyncio.wait_for(future, timeout=self.timeout)

        return msg_id

    async def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe from events.

        Args:
            subscription_id: Subscription ID from subscribe().
        """
        self._subscriptions.pop(subscription_id, None)
        await self.send_command("unsubscribe_events", subscription=subscription_id)

    # High-level API methods

    async def get_states(self) -> list[dict[str, Any]]:
        """Get all entity states."""
        return await self.send_command("get_states")

    async def get_config(self) -> dict[str, Any]:
        """Get Home Assistant configuration."""
        return await self.send_command("get_config")

    async def get_services(self) -> dict[str, Any]:
        """Get all available services."""
        return await self.send_command("get_services")

    async def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> Any:
        """Call a service.

        Args:
            domain: Service domain.
            service: Service name.
            data: Service data.
            target: Service target (entity_id, area_id, etc).
            return_response: Whether to return the service response.

        Returns:
            Service response if return_response is True.
        """
        kwargs: dict[str, Any] = {"domain": domain, "service": service}
        if data:
            kwargs["service_data"] = data
        if target:
            kwargs["target"] = target
        if return_response:
            kwargs["return_response"] = True
        return await self.send_command("call_service", **kwargs)

    async def get_panels(self) -> dict[str, Any]:
        """Get frontend panels."""
        return await self.send_command("get_panels")

    async def ping(self) -> None:
        """Send a ping message."""
        msg_id = self._next_id()
        future: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = future
        await self._send({"id": msg_id, "type": "ping"})
        await asyncio.wait_for(future, timeout=self.timeout)

    # Registry operations

    async def area_registry_list(self) -> list[dict[str, Any]]:
        """List all areas."""
        return await self.send_command("config/area_registry/list")

    async def area_registry_create(
        self,
        name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create an area."""
        return await self.send_command("config/area_registry/create", name=name, **kwargs)

    async def area_registry_update(
        self,
        area_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update an area."""
        return await self.send_command("config/area_registry/update", area_id=area_id, **kwargs)

    async def area_registry_delete(self, area_id: str) -> None:
        """Delete an area."""
        await self.send_command("config/area_registry/delete", area_id=area_id)

    async def floor_registry_list(self) -> list[dict[str, Any]]:
        """List all floors."""
        return await self.send_command("config/floor_registry/list")

    async def floor_registry_create(
        self,
        name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a floor."""
        return await self.send_command("config/floor_registry/create", name=name, **kwargs)

    async def floor_registry_update(
        self,
        floor_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a floor."""
        return await self.send_command("config/floor_registry/update", floor_id=floor_id, **kwargs)

    async def floor_registry_delete(self, floor_id: str) -> None:
        """Delete a floor."""
        await self.send_command("config/floor_registry/delete", floor_id=floor_id)

    async def label_registry_list(self) -> list[dict[str, Any]]:
        """List all labels."""
        return await self.send_command("config/label_registry/list")

    async def label_registry_create(
        self,
        name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a label."""
        return await self.send_command("config/label_registry/create", name=name, **kwargs)

    async def label_registry_update(
        self,
        label_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a label."""
        return await self.send_command("config/label_registry/update", label_id=label_id, **kwargs)

    async def label_registry_delete(self, label_id: str) -> None:
        """Delete a label."""
        await self.send_command("config/label_registry/delete", label_id=label_id)

    async def device_registry_list(self) -> list[dict[str, Any]]:
        """List all devices."""
        return await self.send_command("config/device_registry/list")

    async def device_registry_update(
        self,
        device_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a device."""
        return await self.send_command("config/device_registry/update", device_id=device_id, **kwargs)

    async def entity_registry_list(self) -> list[dict[str, Any]]:
        """List all entities in the registry."""
        return await self.send_command("config/entity_registry/list")

    async def entity_registry_get(self, entity_id: str) -> dict[str, Any]:
        """Get entity registry entry."""
        return await self.send_command("config/entity_registry/get", entity_id=entity_id)

    async def entity_registry_update(
        self,
        entity_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update entity registry entry."""
        return await self.send_command("config/entity_registry/update", entity_id=entity_id, **kwargs)

    async def zone_registry_list(self) -> list[dict[str, Any]]:
        """List all zones."""
        return await self.send_command("zone/list")

    async def zone_create(
        self,
        name: str,
        latitude: float,
        longitude: float,
        radius: float,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a zone."""
        return await self.send_command(
            "zone/create",
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            **kwargs,
        )

    async def zone_update(
        self,
        zone_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a zone."""
        return await self.send_command("zone/update", zone_id=zone_id, **kwargs)

    async def zone_delete(self, zone_id: str) -> None:
        """Delete a zone."""
        await self.send_command("zone/delete", zone_id=zone_id)
