"""Group commands."""

from __future__ import annotations

import json

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def group() -> None:
    """Manage entity groups.

    Create, update, and delete groups.
    """
    pass


@group.command("list")
@pass_context
@handle_errors
@async_command
async def list_groups(ctx: Context) -> None:
    """List all groups."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    # Filter to groups
    groups = [
        s for s in states
        if s.get("entity_id", "").startswith("group.")
    ]

    result = [
        {
            "entity_id": g["entity_id"],
            "name": g.get("attributes", {}).get("friendly_name", ""),
            "state": g.get("state"),
            "entities": g.get("attributes", {}).get("entity_id", []),
        }
        for g in groups
    ]

    print_output(result, text_mode=ctx.text_mode)


@group.command("create")
@click.option("--name", "-n", required=True, help="Group name")
@click.option("--entities", "-e", required=True, help="Comma-separated list of entity IDs")
@click.option("--icon", help="Icon for the group")
@click.option("--all", "all_mode", is_flag=True, help="All entities must be on for group to be on")
@pass_context
@handle_errors
@async_command
async def create_group(
    ctx: Context,
    name: str,
    entities: str,
    icon: str | None,
    all_mode: bool,
) -> None:
    """Create a new group."""
    entity_list = [e.strip() for e in entities.split(",")]

    config = {
        "name": name,
        "entities": entity_list,
    }
    if icon:
        config["icon"] = icon
    if all_mode:
        config["all"] = True

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("group/create", **config)

    print_output(result, text_mode=ctx.text_mode, message=f"Group '{name}' created.")


@group.command("update")
@click.argument("group_id")
@click.option("--name", "-n", help="New name for the group")
@click.option("--entities", "-e", help="Comma-separated list of entity IDs")
@click.option("--add-entities", help="Entities to add (comma-separated)")
@click.option("--remove-entities", help="Entities to remove (comma-separated)")
@click.option("--icon", help="Icon for the group")
@pass_context
@handle_errors
@async_command
async def update_group(
    ctx: Context,
    group_id: str,
    name: str | None,
    entities: str | None,
    add_entities: str | None,
    remove_entities: str | None,
    icon: str | None,
) -> None:
    """Update a group."""
    # Normalize group ID
    if not group_id.startswith("group."):
        group_id = f"group.{group_id}"

    object_id = group_id.split(".", 1)[1]

    config = {}
    if name:
        config["name"] = name
    if icon:
        config["icon"] = icon

    if entities:
        config["entities"] = [e.strip() for e in entities.split(",")]
    elif add_entities or remove_entities:
        # Need to get current entities
        async with ctx.get_ws_client() as ws:
            await ws.connect()
            states = await ws.get_states()

        group_state = next(
            (s for s in states if s.get("entity_id") == group_id),
            None,
        )

        if not group_state:
            from hab.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"Group '{group_id}' not found")

        current = set(group_state.get("attributes", {}).get("entity_id", []))

        if add_entities:
            current.update(e.strip() for e in add_entities.split(","))
        if remove_entities:
            current -= set(e.strip() for e in remove_entities.split(","))

        config["entities"] = list(current)

    if not config:
        from hab.exceptions import ValidationError
        raise ValidationError("No update parameters provided")

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("group/update", object_id=object_id, **config)

    print_output(result, text_mode=ctx.text_mode, message=f"Group '{group_id}' updated.")


@group.command("delete")
@click.argument("group_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_group(ctx: Context, group_id: str, force: bool) -> None:
    """Delete a group."""
    # Normalize group ID
    if not group_id.startswith("group."):
        group_id = f"group.{group_id}"

    object_id = group_id.split(".", 1)[1]

    if not force and not ctx.text_mode:
        click.confirm(f"Delete group {group_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command("group/delete", object_id=object_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Group '{group_id}' deleted.")
