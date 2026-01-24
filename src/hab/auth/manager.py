"""Authentication state management."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from hab.auth.credentials import Credentials, delete_credentials, load_credentials, save_credentials
from hab.exceptions import AuthenticationError

if TYPE_CHECKING:
    from hab.client.rest import RestClient


class AuthManager:
    """Manages authentication state and token refresh."""

    def __init__(self, config_dir: str | None = None) -> None:
        """Initialize the auth manager.

        Args:
            config_dir: Optional custom configuration directory.
        """
        self.config_dir = config_dir
        self._credentials: Credentials | None = None

    @property
    def credentials(self) -> Credentials | None:
        """Get current credentials."""
        if self._credentials is None:
            self._credentials = load_credentials(self.config_dir)
        return self._credentials

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.credentials is not None and self.credentials.has_valid_token

    @property
    def url(self) -> str | None:
        """Get Home Assistant URL."""
        return self.credentials.url if self.credentials else None

    @property
    def token(self) -> str | None:
        """Get access token."""
        return self.credentials.access_token if self.credentials else None

    def needs_refresh(self) -> bool:
        """Check if token needs refresh.

        Returns:
            True if token is expired or about to expire.
        """
        if not self.credentials:
            return False

        if not self.credentials.is_oauth:
            return False  # Long-lived tokens don't expire

        if not self.credentials.token_expiry:
            return True  # No expiry info, assume needs refresh

        # Refresh if within 5 minutes of expiry
        return time.time() >= (self.credentials.token_expiry - 300)

    async def refresh_token(self, client: RestClient) -> None:
        """Refresh OAuth token.

        Args:
            client: REST client to use for refresh.

        Raises:
            AuthenticationError: If refresh fails.
        """
        if not self.credentials or not self.credentials.refresh_token:
            raise AuthenticationError("No refresh token available")

        from hab.auth.oauth import refresh_access_token

        new_creds = await refresh_access_token(
            self.credentials.url,
            self.credentials.refresh_token,
        )
        self._credentials = new_creds
        save_credentials(new_creds, self.config_dir)

    def save(self, credentials: Credentials) -> None:
        """Save new credentials.

        Args:
            credentials: Credentials to save.
        """
        self._credentials = credentials
        save_credentials(credentials, self.config_dir)

    def logout(self) -> bool:
        """Remove stored credentials.

        Returns:
            True if credentials were removed.
        """
        self._credentials = None
        return delete_credentials(self.config_dir)

    def get_auth_status(self) -> dict:
        """Get authentication status as a dict.

        Returns:
            Dictionary with authentication status information.
        """
        if not self.credentials:
            return {
                "authenticated": False,
                "message": "Not authenticated. Run 'hab auth login' to authenticate.",
            }

        return {
            "authenticated": True,
            "url": self.credentials.url,
            "auth_type": "oauth" if self.credentials.is_oauth else "token",
            "token_expiry": self.credentials.token_expiry,
        }
