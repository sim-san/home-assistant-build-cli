"""Floor commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def floor() -> None:
    """Manage floors.

    Create, update, and delete floors.
    """
    pass


@floor.command("list")
@pass_context
@handle_errors
@async_command
async def list_floors(ctx: Context) -> None:
    """List all floors."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        floors = await ws.floor_registry_list()

    result = [
        {
            "floor_id": f["floor_id"],
            "name": f["name"],
            "level": f.get("level"),
            "icon": f.get("icon"),
        }
        for f in floors
    ]

    print_output(result, text_mode=ctx.text_mode)


@floor.command("create")
@click.argument("name")
@click.option("--level", type=int, help="Floor level (integer)")
@click.option("--icon", help="Icon for the floor")
@pass_context
@handle_errors
@async_command
async def create_floor(
    ctx: Context,
    name: str,
    level: int | None,
    icon: str | None,
) -> None:
    """Create a new floor."""
    kwargs = {}
    if level is not None:
        kwargs["level"] = level
    if icon:
        kwargs["icon"] = icon

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.floor_registry_create(name, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Floor '{name}' created.")


@floor.command("update")
@click.argument("floor_id")
@click.option("--name", help="New name for the floor")
@click.option("--level", type=int, help="Floor level (integer)")
@click.option("--icon", help="Icon for the floor")
@pass_context
@handle_errors
@async_command
async def update_floor(
    ctx: Context,
    floor_id: str,
    name: str | None,
    level: int | None,
    icon: str | None,
) -> None:
    """Update a floor."""
    kwargs = {}
    if name:
        kwargs["name"] = name
    if level is not None:
        kwargs["level"] = level
    if icon:
        kwargs["icon"] = icon

    if not kwargs:
        from hab.exceptions import ValidationError
        raise ValidationError("No update parameters provided")

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.floor_registry_update(floor_id, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Floor '{floor_id}' updated.")


@floor.command("delete")
@click.argument("floor_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_floor(ctx: Context, floor_id: str, force: bool) -> None:
    """Delete a floor."""
    if not force and not ctx.text_mode:
        click.confirm(f"Delete floor {floor_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.floor_registry_delete(floor_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Floor '{floor_id}' deleted.")
