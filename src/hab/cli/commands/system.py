"""System commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def system() -> None:
    """System operations.

    View system info, check config, restart, and more.
    """
    pass


@system.command("info")
@pass_context
@handle_errors
@async_command
async def system_info(ctx: Context) -> None:
    """Get system information."""
    client = ctx.get_rest_client()
    async with client:
        config = await client.get_config()

    result = {
        "location_name": config.get("location_name"),
        "version": config.get("version"),
        "state": config.get("state"),
        "external_url": config.get("external_url"),
        "internal_url": config.get("internal_url"),
        "time_zone": config.get("time_zone"),
        "unit_system": config.get("unit_system"),
        "elevation": config.get("elevation"),
        "latitude": config.get("latitude"),
        "longitude": config.get("longitude"),
    }

    print_output(result, text_mode=ctx.text_mode)


@system.command("health")
@pass_context
@handle_errors
@async_command
async def system_health(ctx: Context) -> None:
    """Get system health status."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("system_health/info")

    print_output(result, text_mode=ctx.text_mode)


@system.command("config-check")
@pass_context
@handle_errors
@async_command
async def config_check(ctx: Context) -> None:
    """Validate Home Assistant configuration."""
    client = ctx.get_rest_client()
    async with client:
        result = await client.check_config()

    if result.get("result") == "valid":
        print_output(
            {"valid": True, "errors": None},
            text_mode=ctx.text_mode,
            message="Configuration is valid.",
        )
    else:
        print_output(
            {"valid": False, "errors": result.get("errors")},
            text_mode=ctx.text_mode,
            success=False,
        )


@system.command("restart")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def restart(ctx: Context, force: bool) -> None:
    """Restart Home Assistant."""
    if not force:
        click.confirm("This will restart Home Assistant. Continue?", abort=True)

    client = ctx.get_rest_client()
    async with client:
        await client.restart()

    print_output(None, text_mode=ctx.text_mode, message="Restart initiated.")


@system.command("logs")
@click.option("--lines", "-n", default=100, help="Number of lines to show")
@pass_context
@handle_errors
@async_command
async def logs(ctx: Context, lines: int) -> None:
    """Get error logs."""
    client = ctx.get_rest_client()
    async with client:
        log_content = await client.get_error_log()

    # Get last N lines
    log_lines = log_content.strip().split("\n")
    if len(log_lines) > lines:
        log_lines = log_lines[-lines:]

    print_output("\n".join(log_lines), text_mode=ctx.text_mode)


@system.command("updates")
@pass_context
@handle_errors
@async_command
async def updates(ctx: Context) -> None:
    """Check for available updates."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    # Find update entities
    updates = [
        {
            "entity_id": s["entity_id"],
            "title": s.get("attributes", {}).get("title", s["entity_id"]),
            "installed_version": s.get("attributes", {}).get("installed_version"),
            "latest_version": s.get("attributes", {}).get("latest_version"),
            "update_available": s.get("state") == "on",
        }
        for s in states
        if s.get("entity_id", "").startswith("update.")
    ]

    print_output(updates, text_mode=ctx.text_mode)
