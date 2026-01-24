"""Credential storage with encryption."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import uuid
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field

from hab.config.paths import get_credentials_path


def _get_machine_id() -> str:
    """Get a machine-specific identifier for key derivation.

    Returns:
        A string that is unique to this machine.
    """
    # Combine multiple sources for a stable machine identifier
    sources = [
        platform.node(),  # Hostname
        str(uuid.getnode()),  # MAC address
    ]

    # Try to get additional system-specific identifiers
    try:
        if platform.system() == "Darwin":
            # macOS: use hardware UUID
            import subprocess

            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "IOPlatformUUID" in line:
                        sources.append(line.split('"')[-2])
                        break
    except (OSError, subprocess.TimeoutExpired):
        pass

    return "|".join(sources)


def _derive_key() -> bytes:
    """Derive an encryption key from machine-specific data.

    Returns:
        A 32-byte key suitable for Fernet encryption.
    """
    machine_id = _get_machine_id()
    # Use SHA-256 to derive a consistent key
    key_material = hashlib.sha256(machine_id.encode()).digest()
    # Fernet requires base64-encoded 32-byte key
    return base64.urlsafe_b64encode(key_material)


class Credentials(BaseModel):
    """Stored credentials for Home Assistant authentication."""

    url: str = Field(description="Home Assistant URL")
    access_token: str | None = Field(default=None, description="Long-lived access token")
    refresh_token: str | None = Field(default=None, description="OAuth refresh token")
    token_expiry: float | None = Field(default=None, description="Token expiry timestamp")

    @property
    def is_oauth(self) -> bool:
        """Check if using OAuth authentication."""
        return self.refresh_token is not None

    @property
    def has_valid_token(self) -> bool:
        """Check if there is a valid access token."""
        return self.access_token is not None


def load_credentials(config_dir: str | None = None) -> Credentials | None:
    """Load credentials from encrypted storage.

    Args:
        config_dir: Optional custom configuration directory.

    Returns:
        Credentials if found and decrypted successfully, None otherwise.
    """
    # First check environment variables
    env_url = os.environ.get("HAB_URL")
    env_token = os.environ.get("HAB_TOKEN")

    if env_url and env_token:
        return Credentials(url=env_url, access_token=env_token)

    # Check for refresh token in environment
    env_refresh = os.environ.get("HAB_REFRESH_TOKEN")
    if env_url and env_refresh:
        return Credentials(url=env_url, refresh_token=env_refresh)

    # Load from file
    creds_path = get_credentials_path(config_dir)
    if not creds_path.exists():
        return None

    try:
        encrypted_data = creds_path.read_bytes()
        fernet = Fernet(_derive_key())
        decrypted = fernet.decrypt(encrypted_data)
        data = json.loads(decrypted.decode())
        return Credentials(**data)
    except (InvalidToken, json.JSONDecodeError, OSError):
        return None


def save_credentials(credentials: Credentials, config_dir: str | None = None) -> None:
    """Save credentials to encrypted storage.

    Args:
        credentials: Credentials to save.
        config_dir: Optional custom configuration directory.
    """
    creds_path = get_credentials_path(config_dir)
    creds_path.parent.mkdir(parents=True, exist_ok=True)

    # Encrypt the credentials
    fernet = Fernet(_derive_key())
    data = json.dumps(credentials.model_dump()).encode()
    encrypted = fernet.encrypt(data)

    # Write with restrictive permissions
    creds_path.write_bytes(encrypted)
    os.chmod(creds_path, 0o600)


def delete_credentials(config_dir: str | None = None) -> bool:
    """Delete stored credentials.

    Args:
        config_dir: Optional custom configuration directory.

    Returns:
        True if credentials were deleted, False if they didn't exist.
    """
    creds_path = get_credentials_path(config_dir)
    if creds_path.exists():
        creds_path.unlink()
        return True
    return False
