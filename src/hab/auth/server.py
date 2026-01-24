"""Temporary OAuth callback server."""

from __future__ import annotations

import asyncio
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlparse


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET request (OAuth callback)."""
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        # Extract single values from lists
        result = {
            "code": params.get("code", [None])[0],
            "state": params.get("state", [None])[0],
            "error": params.get("error", [None])[0],
        }

        # Store result on server instance
        self.server.callback_result = result  # type: ignore

        # Send success response
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if result.get("error"):
            html = """
            <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>You can close this window.</p>
            </body>
            </html>
            """.format(error=result["error"])
        else:
            html = """
            <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """

        self.wfile.write(html.encode())

        # Signal that we have a result
        self.server.has_result = True  # type: ignore


def _get_local_ip() -> str:
    """Get the local network IP address.

    This is needed for OAuth callbacks when using SSH.

    Returns:
        Local IP address.
    """
    try:
        # Create a socket and connect to an external address
        # This doesn't actually send data, just determines the route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _find_available_port() -> int:
    """Find an available port.

    Returns:
        Available port number.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class OAuthCallbackServer:
    """Temporary HTTP server for OAuth callbacks."""

    def __init__(self) -> None:
        """Initialize the callback server."""
        self._server: HTTPServer | None = None
        self._thread: Thread | None = None
        self._ip: str = ""
        self._port: int = 0

    async def start(self) -> str:
        """Start the callback server.

        Returns:
            Callback URL to use in OAuth flow.
        """
        self._ip = _get_local_ip()
        self._port = _find_available_port()

        self._server = HTTPServer((self._ip, self._port), OAuthCallbackHandler)
        self._server.callback_result = None  # type: ignore
        self._server.has_result = False  # type: ignore

        self._thread = Thread(target=self._server.serve_forever)
        self._thread.daemon = True
        self._thread.start()

        return f"http://{self._ip}:{self._port}/callback"

    async def wait_for_callback(self, timeout: float = 300) -> dict[str, Any]:
        """Wait for OAuth callback.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            Callback parameters.

        Raises:
            TimeoutError: If callback not received within timeout.
        """
        if not self._server:
            raise RuntimeError("Server not started")

        elapsed = 0.0
        interval = 0.5

        while elapsed < timeout:
            if self._server.has_result:  # type: ignore
                return self._server.callback_result  # type: ignore
            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError("OAuth callback not received within timeout")

    async def stop(self) -> None:
        """Stop the callback server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None
