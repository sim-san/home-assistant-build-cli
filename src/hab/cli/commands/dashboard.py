"""Dashboard commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.input import parse_input
from hab.utils.output import print_output


@click.group()
def dashboard() -> None:
    """Manage dashboards.

    Create, update, and delete Lovelace dashboards.
    """
    pass


@dashboard.command("list")
@pass_context
@handle_errors
@async_command
async def list_dashboards(ctx: Context) -> None:
    """List all dashboards."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("lovelace/dashboards/list")

    dashboards = [
        {
            "url_path": d.get("url_path") or "lovelace",
            "title": d.get("title", ""),
            "mode": d.get("mode", "storage"),
            "require_admin": d.get("require_admin", False),
            "show_in_sidebar": d.get("show_in_sidebar", True),
        }
        for d in result
    ]

    print_output(dashboards, text_mode=ctx.text_mode)


@dashboard.command("get")
@click.argument("url_path")
@pass_context
@handle_errors
@async_command
async def get_dashboard(ctx: Context, url_path: str) -> None:
    """Get dashboard configuration.

    URL_PATH is the dashboard URL path (e.g., 'lovelace' for default).
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command(
            "lovelace/config",
            url_path=url_path if url_path != "lovelace" else None,
        )

    print_output(result, text_mode=ctx.text_mode)


@dashboard.command("create")
@click.option("--url-path", required=True, help="URL path for the dashboard")
@click.option("--title", required=True, help="Dashboard title")
@click.option("--icon", help="Dashboard icon")
@click.option("--require-admin", is_flag=True, help="Require admin access")
@click.option("--show-in-sidebar/--hide-from-sidebar", default=True, help="Show in sidebar")
@pass_context
@handle_errors
@async_command
async def create_dashboard(
    ctx: Context,
    url_path: str,
    title: str,
    icon: str | None,
    require_admin: bool,
    show_in_sidebar: bool,
) -> None:
    """Create a new dashboard."""
    config = {
        "url_path": url_path,
        "title": title,
        "require_admin": require_admin,
        "show_in_sidebar": show_in_sidebar,
    }
    if icon:
        config["icon"] = icon

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("lovelace/dashboards/create", **config)

    print_output(result, text_mode=ctx.text_mode, message=f"Dashboard '{title}' created.")


@dashboard.command("update")
@click.argument("url_path")
@click.option("--title", help="Dashboard title")
@click.option("--icon", help="Dashboard icon")
@click.option("--require-admin/--no-require-admin", default=None, help="Require admin access")
@click.option("--show-in-sidebar/--hide-from-sidebar", default=None, help="Show in sidebar")
@click.option("--data", "-d", help="Dashboard configuration as JSON")
@click.option("--file", "-f", "file_path", type=click.Path(exists=True), help="Path to config file")
@pass_context
@handle_errors
@async_command
async def update_dashboard(
    ctx: Context,
    url_path: str,
    title: str | None,
    icon: str | None,
    require_admin: bool | None,
    show_in_sidebar: bool | None,
    data: str | None,
    file_path: str | None,
) -> None:
    """Update a dashboard.

    Use --data or --file to update the dashboard's Lovelace configuration.
    Use other options to update dashboard metadata.
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()

        # Update dashboard metadata if any options provided
        meta_update = {}
        if title:
            meta_update["title"] = title
        if icon:
            meta_update["icon"] = icon
        if require_admin is not None:
            meta_update["require_admin"] = require_admin
        if show_in_sidebar is not None:
            meta_update["show_in_sidebar"] = show_in_sidebar

        if meta_update:
            await ws.send_command(
                "lovelace/dashboards/update",
                dashboard_id=url_path,
                **meta_update,
            )

        # Update Lovelace config if data provided
        if data or file_path:
            config = parse_input(data=data, file=file_path)
            await ws.send_command(
                "lovelace/config/save",
                url_path=url_path if url_path != "lovelace" else None,
                config=config,
            )

    print_output(None, text_mode=ctx.text_mode, message=f"Dashboard '{url_path}' updated.")


@dashboard.command("delete")
@click.argument("url_path")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_dashboard(ctx: Context, url_path: str, force: bool) -> None:
    """Delete a dashboard."""
    if not force and not ctx.text_mode:
        click.confirm(f"Delete dashboard {url_path}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command("lovelace/dashboards/delete", dashboard_id=url_path)

    print_output(None, text_mode=ctx.text_mode, message=f"Dashboard '{url_path}' deleted.")


@dashboard.command("card-types")
@pass_context
@handle_errors
@async_command
async def card_types(ctx: Context) -> None:
    """List available card types with documentation."""
    # Standard Lovelace card types
    cards = [
        {"type": "alarm-panel", "description": "Alarm panel card for arming/disarming"},
        {"type": "button", "description": "Simple button to trigger actions"},
        {"type": "calendar", "description": "Calendar view card"},
        {"type": "entities", "description": "List of entity rows"},
        {"type": "entity", "description": "Single entity state card"},
        {"type": "gauge", "description": "Gauge visualization for numeric values"},
        {"type": "glance", "description": "Compact grid of entities"},
        {"type": "grid", "description": "Grid layout for cards"},
        {"type": "history-graph", "description": "Entity state history graph"},
        {"type": "horizontal-stack", "description": "Horizontal card layout"},
        {"type": "humidifier", "description": "Humidifier control card"},
        {"type": "iframe", "description": "Embedded webpage"},
        {"type": "light", "description": "Light control card"},
        {"type": "logbook", "description": "Logbook entries"},
        {"type": "map", "description": "Map with entity locations"},
        {"type": "markdown", "description": "Markdown text content"},
        {"type": "media-control", "description": "Media player control"},
        {"type": "picture", "description": "Static picture"},
        {"type": "picture-elements", "description": "Picture with interactive elements"},
        {"type": "picture-entity", "description": "Entity state on picture"},
        {"type": "picture-glance", "description": "Picture with entity states"},
        {"type": "plant-status", "description": "Plant monitoring card"},
        {"type": "sensor", "description": "Sensor value display"},
        {"type": "shopping-list", "description": "Shopping list card"},
        {"type": "statistic", "description": "Statistics display"},
        {"type": "statistics-graph", "description": "Statistics graph"},
        {"type": "thermostat", "description": "Climate control card"},
        {"type": "tile", "description": "Modern tile card"},
        {"type": "vertical-stack", "description": "Vertical card layout"},
        {"type": "weather-forecast", "description": "Weather forecast card"},
    ]

    print_output(cards, text_mode=ctx.text_mode)
