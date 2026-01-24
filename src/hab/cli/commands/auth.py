"""Authentication commands."""

from __future__ import annotations

import click

from hab.auth.credentials import Credentials
from hab.auth.oauth import run_oauth_flow
from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def auth() -> None:
    """Authentication management.

    Manage authentication with Home Assistant.
    """
    pass


@auth.command()
@click.option(
    "--token",
    is_flag=True,
    help="Use long-lived access token instead of OAuth",
)
@click.option(
    "--url",
    help="Home Assistant URL",
)
@click.option(
    "--access-token",
    help="Long-lived access token (non-interactive mode)",
)
@pass_context
@handle_errors
@async_command
async def login(
    ctx: Context,
    token: bool,
    url: str | None,
    access_token: str | None,
) -> None:
    """Authenticate with Home Assistant.

    By default, uses OAuth flow. Use --token for long-lived access token.
    """
    if token:
        # Token-based authentication
        if not url:
            url = click.prompt("Home Assistant URL")
        if not access_token:
            access_token = click.prompt("Long-lived access token", hide_input=True)

        credentials = Credentials(url=url, access_token=access_token)

        # Validate the token by making a test request
        from hab.client import RestClient

        async with RestClient(url=url, token=access_token) as client:
            config = await client.get_config()

        ctx.auth.save(credentials)
        print_output(
            {
                "url": url,
                "location_name": config.get("location_name", "Home"),
                "version": config.get("version"),
            },
            text_mode=ctx.text_mode,
            message=f"Successfully authenticated to {config.get('location_name', 'Home Assistant')}",
        )
    else:
        # OAuth flow
        if not url:
            url = click.prompt("Home Assistant URL")

        credentials = await run_oauth_flow(url)

        # Validate and get info
        from hab.client import RestClient

        async with RestClient(url=url, token=credentials.access_token) as client:  # type: ignore
            config = await client.get_config()

        ctx.auth.save(credentials)
        print_output(
            {
                "url": url,
                "location_name": config.get("location_name", "Home"),
                "version": config.get("version"),
            },
            text_mode=ctx.text_mode,
            message=f"Successfully authenticated to {config.get('location_name', 'Home Assistant')}",
        )


@auth.command()
@pass_context
@handle_errors
def logout(ctx: Context) -> None:
    """Remove stored credentials."""
    if ctx.auth.logout():
        print_output(
            None,
            text_mode=ctx.text_mode,
            message="Successfully logged out.",
        )
    else:
        print_output(
            None,
            text_mode=ctx.text_mode,
            message="No credentials to remove.",
        )


@auth.command()
@pass_context
@handle_errors
def status(ctx: Context) -> None:
    """Show current authentication status."""
    status_data = ctx.auth.get_auth_status()
    print_output(status_data, text_mode=ctx.text_mode)


@auth.command()
@pass_context
@handle_errors
@async_command
async def refresh(ctx: Context) -> None:
    """Force token refresh (OAuth only)."""
    if not ctx.auth.credentials:
        from hab.exceptions import AuthenticationError

        raise AuthenticationError("Not authenticated")

    if not ctx.auth.credentials.is_oauth:
        from hab.exceptions import ValidationError

        raise ValidationError("Token refresh is only available for OAuth authentication")

    client = ctx.get_rest_client()
    await ctx.auth.refresh_token(client)

    print_output(
        {"token_expiry": ctx.auth.credentials.token_expiry},
        text_mode=ctx.text_mode,
        message="Token refreshed successfully.",
    )
