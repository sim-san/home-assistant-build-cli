"""Configuration file paths using platformdirs."""

from pathlib import Path

import platformdirs

APP_NAME = "home-assistant-builder"
APP_AUTHOR = "home-assistant"


def get_config_dir(custom_path: str | None = None) -> Path:
    """Get the configuration directory path.

    Args:
        custom_path: Optional custom path to use instead of default.

    Returns:
        Path to the configuration directory.
    """
    if custom_path:
        return Path(custom_path).expanduser()
    return Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR))


def get_config_path(custom_dir: str | None = None) -> Path:
    """Get the path to config.json.

    Args:
        custom_dir: Optional custom configuration directory.

    Returns:
        Path to config.json.
    """
    return get_config_dir(custom_dir) / "config.json"


def get_credentials_path(custom_dir: str | None = None) -> Path:
    """Get the path to credentials.json.

    Args:
        custom_dir: Optional custom configuration directory.

    Returns:
        Path to credentials.json.
    """
    return get_config_dir(custom_dir) / "credentials.json"
