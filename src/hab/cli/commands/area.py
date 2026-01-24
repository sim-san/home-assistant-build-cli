"""Area commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def area() -> None:
    """Manage areas.

    Create, update, and delete areas.
    """
    pass


@area.command("list")
@pass_context
@handle_errors
@async_command
async def list_areas(ctx: Context) -> None:
    """List all areas."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        areas = await ws.area_registry_list()

    result = [
        {
            "area_id": a["area_id"],
            "name": a["name"],
            "floor_id": a.get("floor_id"),
            "icon": a.get("icon"),
            "labels": a.get("labels", []),
        }
        for a in areas
    ]

    print_output(result, text_mode=ctx.text_mode)


@area.command("create")
@click.argument("name")
@click.option("--floor", "floor_id", help="Floor ID to assign")
@click.option("--icon", help="Icon for the area")
@pass_context
@handle_errors
@async_command
async def create_area(
    ctx: Context,
    name: str,
    floor_id: str | None,
    icon: str | None,
) -> None:
    """Create a new area."""
    kwargs = {}
    if floor_id:
        kwargs["floor_id"] = floor_id
    if icon:
        kwargs["icon"] = icon

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.area_registry_create(name, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Area '{name}' created.")


@area.command("update")
@click.argument("area_id")
@click.option("--name", help="New name for the area")
@click.option("--floor", "floor_id", help="Floor ID to assign")
@click.option("--icon", help="Icon for the area")
@pass_context
@handle_errors
@async_command
async def update_area(
    ctx: Context,
    area_id: str,
    name: str | None,
    floor_id: str | None,
    icon: str | None,
) -> None:
    """Update an area."""
    kwargs = {}
    if name:
        kwargs["name"] = name
    if floor_id:
        kwargs["floor_id"] = floor_id
    if icon:
        kwargs["icon"] = icon

    if not kwargs:
        from hab.exceptions import ValidationError
        raise ValidationError("No update parameters provided")

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.area_registry_update(area_id, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Area '{area_id}' updated.")


@area.command("delete")
@click.argument("area_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_area(ctx: Context, area_id: str, force: bool) -> None:
    """Delete an area."""
    if not force and not ctx.text_mode:
        click.confirm(f"Delete area {area_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.area_registry_delete(area_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Area '{area_id}' deleted.")
