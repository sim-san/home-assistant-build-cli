"""OAuth2 authentication flow."""

from __future__ import annotations

import secrets
import time
import urllib.parse
import webbrowser
from typing import Any

import httpx

from hab.auth.credentials import Credentials
from hab.auth.server import OAuthCallbackServer
from hab.exceptions import AuthenticationError


CLIENT_ID = "https://github.com/home-assistant/hab"
AUTHORIZE_PATH = "/auth/authorize"
TOKEN_PATH = "/auth/token"


def get_authorize_url(
    ha_url: str,
    redirect_uri: str,
    state: str,
) -> str:
    """Build the OAuth authorization URL.

    Args:
        ha_url: Home Assistant URL.
        redirect_uri: Callback URL for the OAuth flow.
        state: Random state for CSRF protection.

    Returns:
        Full authorization URL.
    """
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    }
    query = urllib.parse.urlencode(params)
    return f"{ha_url.rstrip('/')}{AUTHORIZE_PATH}?{query}"


async def exchange_code_for_tokens(
    ha_url: str,
    code: str,
    redirect_uri: str,
) -> Credentials:
    """Exchange authorization code for tokens.

    Args:
        ha_url: Home Assistant URL.
        code: Authorization code from callback.
        redirect_uri: Callback URL used in the flow.

    Returns:
        Credentials with access and refresh tokens.

    Raises:
        AuthenticationError: If token exchange fails.
    """
    token_url = f"{ha_url.rstrip('/')}{TOKEN_PATH}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "redirect_uri": redirect_uri,
            },
        )

        if response.status_code != 200:
            raise AuthenticationError(f"Token exchange failed: {response.text}")

        data = response.json()

    expires_in = data.get("expires_in", 1800)
    token_expiry = time.time() + expires_in

    return Credentials(
        url=ha_url,
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        token_expiry=token_expiry,
    )


async def refresh_access_token(
    ha_url: str,
    refresh_token: str,
) -> Credentials:
    """Refresh an expired access token.

    Args:
        ha_url: Home Assistant URL.
        refresh_token: Refresh token.

    Returns:
        Credentials with new access token.

    Raises:
        AuthenticationError: If refresh fails.
    """
    token_url = f"{ha_url.rstrip('/')}{TOKEN_PATH}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": CLIENT_ID,
            },
        )

        if response.status_code != 200:
            raise AuthenticationError(f"Token refresh failed: {response.text}")

        data = response.json()

    expires_in = data.get("expires_in", 1800)
    token_expiry = time.time() + expires_in

    return Credentials(
        url=ha_url,
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", refresh_token),
        token_expiry=token_expiry,
    )


async def run_oauth_flow(ha_url: str) -> Credentials:
    """Run the full OAuth flow.

    This starts a temporary HTTP server, opens the browser for authorization,
    and waits for the callback.

    Args:
        ha_url: Home Assistant URL.

    Returns:
        Credentials after successful authentication.

    Raises:
        AuthenticationError: If authentication fails.
    """
    state = secrets.token_urlsafe(32)

    server = OAuthCallbackServer()
    redirect_uri = await server.start()

    authorize_url = get_authorize_url(ha_url, redirect_uri, state)

    print(f"\nOpening browser for authentication...")
    print(f"If browser doesn't open, visit: {authorize_url}\n")

    webbrowser.open(authorize_url)

    try:
        result = await server.wait_for_callback(timeout=300)
    finally:
        await server.stop()

    if result.get("error"):
        raise AuthenticationError(f"OAuth error: {result['error']}")

    if result.get("state") != state:
        raise AuthenticationError("State mismatch - possible CSRF attack")

    if not result.get("code"):
        raise AuthenticationError("No authorization code received")

    return await exchange_code_for_tokens(ha_url, result["code"], redirect_uri)
