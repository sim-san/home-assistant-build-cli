"""Main CLI entry point."""

from __future__ import annotations

import asyncio
import sys
from functools import wraps
from typing import Any, Callable, TypeVar

import click

from hab import __version__
from hab.auth import AuthManager
from hab.client import RestClient, WebSocketClient
from hab.config import Settings, get_settings
from hab.exceptions import ExitCode, HabError
from hab.utils.output import format_error, print_error

F = TypeVar("F", bound=Callable[..., Any])


class Context:
    """CLI context object passed to commands."""

    def __init__(
        self,
        config_dir: str | None = None,
        text_mode: bool = False,
        verbose: bool = False,
    ) -> None:
        """Initialize context.

        Args:
            config_dir: Custom configuration directory.
            text_mode: Use text output instead of JSON.
            verbose: Enable verbose output.
        """
        self.config_dir = config_dir
        self.text_mode = text_mode
        self.verbose = verbose
        self._settings: Settings | None = None
        self._auth_manager: AuthManager | None = None
        self._rest_client: RestClient | None = None
        self._ws_client: WebSocketClient | None = None

    @property
    def settings(self) -> Settings:
        """Get settings."""
        if self._settings is None:
            self._settings = get_settings(self.config_dir)
        return self._settings

    @property
    def auth(self) -> AuthManager:
        """Get auth manager."""
        if self._auth_manager is None:
            self._auth_manager = AuthManager(self.config_dir)
        return self._auth_manager

    def get_rest_client(self) -> RestClient:
        """Get REST client.

        Returns:
            REST client.

        Raises:
            HabError: If not authenticated.
        """
        if not self.auth.is_authenticated:
            from hab.exceptions import AuthenticationError
            raise AuthenticationError(
                "Not authenticated. Run 'hab auth login' to authenticate."
            )

        return RestClient(
            url=self.auth.url,  # type: ignore
            token=self.auth.token,  # type: ignore
            timeout=self.settings.timeout,
            verify_ssl=self.settings.verify_ssl,
        )

    def get_ws_client(self) -> WebSocketClient:
        """Get WebSocket client.

        Returns:
            WebSocket client.

        Raises:
            HabError: If not authenticated.
        """
        if not self.auth.is_authenticated:
            from hab.exceptions import AuthenticationError
            raise AuthenticationError(
                "Not authenticated. Run 'hab auth login' to authenticate."
            )

        return WebSocketClient(
            url=self.auth.url,  # type: ignore
            token=self.auth.token,  # type: ignore
            timeout=self.settings.timeout,
            verify_ssl=self.settings.verify_ssl,
        )


pass_context = click.make_pass_decorator(Context, ensure=True)


def async_command(f: F) -> F:
    """Decorator to run async commands."""

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))

    return wrapper  # type: ignore


def handle_errors(f: F) -> F:
    """Decorator to handle errors and format output."""

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = None
        for arg in args:
            if isinstance(arg, Context):
                ctx = arg
                break

        try:
            return f(*args, **kwargs)
        except HabError as e:
            text_mode = ctx.text_mode if ctx else False
            print_error(e, text_mode=text_mode, code=e.error_code, details=e.details)
            sys.exit(e.exit_code)
        except Exception as e:
            text_mode = ctx.text_mode if ctx else False
            print_error(e, text_mode=text_mode)
            sys.exit(ExitCode.GENERAL_ERROR)

    return wrapper  # type: ignore


@click.group()
@click.option(
    "--config",
    "config_dir",
    type=click.Path(),
    envvar="HAB_CONFIG_DIR",
    help="Path to config directory (default: ~/.config/home-assistant-builder)",
)
@click.option(
    "--json",
    "json_mode",
    is_flag=True,
    default=True,
    hidden=True,
    help="Force JSON output (default)",
)
@click.option(
    "--text",
    "text_mode",
    is_flag=True,
    help="Use human-readable text output",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output",
)
@click.version_option(version=__version__, prog_name="hab")
@click.pass_context
def cli(
    ctx: click.Context,
    config_dir: str | None,
    json_mode: bool,
    text_mode: bool,
    verbose: bool,
) -> None:
    """Home Assistant Builder - Build Home Assistant configurations.

    A CLI utility designed for LLMs to build and manage Home Assistant configurations.
    """
    ctx.obj = Context(
        config_dir=config_dir,
        text_mode=text_mode,
        verbose=verbose,
    )


# Import and register command groups
from hab.cli.commands import (
    action,
    area,
    auth,
    automation,
    backup,
    blueprint,
    calendar,
    dashboard,
    device,
    entity,
    floor,
    group,
    helper,
    label,
    script,
    system,
    thread,
    zone,
)

cli.add_command(auth.auth)
cli.add_command(automation.automation)
cli.add_command(script.script)
cli.add_command(entity.entity)
cli.add_command(action.action)
cli.add_command(area.area)
cli.add_command(floor.floor)
cli.add_command(zone.zone)
cli.add_command(label.label)
cli.add_command(helper.helper)
cli.add_command(dashboard.dashboard)
cli.add_command(backup.backup)
cli.add_command(calendar.calendar)
cli.add_command(blueprint.blueprint)
cli.add_command(system.system)
cli.add_command(device.device)
cli.add_command(group.group)
cli.add_command(thread.thread)


if __name__ == "__main__":
    cli()
