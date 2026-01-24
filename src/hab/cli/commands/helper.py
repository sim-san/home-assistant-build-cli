"""Helper entity commands."""

from __future__ import annotations

import json

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


HELPER_TYPES = [
    "input_boolean",
    "input_number",
    "input_text",
    "input_select",
    "input_datetime",
    "input_button",
    "counter",
    "timer",
    "schedule",
]


@click.group()
def helper() -> None:
    """Manage helper entities.

    Create, update, and delete helper entities like input_boolean, counter, etc.
    """
    pass


@helper.command("list")
@click.argument("helper_type", required=False)
@pass_context
@handle_errors
@async_command
async def list_helpers(ctx: Context, helper_type: str | None) -> None:
    """List helper entities.

    Optionally filter by HELPER_TYPE (input_boolean, counter, etc).
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    # Filter to helpers
    helpers = []
    for state in states:
        entity_id = state.get("entity_id", "")
        domain = entity_id.split(".")[0] if "." in entity_id else ""

        if domain not in HELPER_TYPES:
            continue

        if helper_type and domain != helper_type:
            continue

        helpers.append({
            "entity_id": entity_id,
            "type": domain,
            "name": state.get("attributes", {}).get("friendly_name", ""),
            "state": state.get("state"),
        })

    print_output(helpers, text_mode=ctx.text_mode)


@helper.command("create")
@click.argument("helper_type", type=click.Choice(HELPER_TYPES))
@click.option("--name", "-n", required=True, help="Name for the helper")
@click.option("--icon", help="Icon for the helper")
@click.option("--data", "-d", help="Additional configuration as JSON")
@pass_context
@handle_errors
@async_command
async def create_helper(
    ctx: Context,
    helper_type: str,
    name: str,
    icon: str | None,
    data: str | None,
) -> None:
    """Create a helper entity.

    HELPER_TYPE must be one of: input_boolean, input_number, input_text,
    input_select, input_datetime, input_button, counter, timer, schedule.
    """
    config = {"name": name}
    if icon:
        config["icon"] = icon

    if data:
        extra = json.loads(data)
        config.update(extra)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command(f"{helper_type}/create", **config)

    print_output(result, text_mode=ctx.text_mode, message=f"Helper '{name}' created.")


@helper.command("update")
@click.argument("entity_id")
@click.option("--name", "-n", help="New name for the helper")
@click.option("--icon", help="Icon for the helper")
@click.option("--data", "-d", help="Additional configuration as JSON")
@pass_context
@handle_errors
@async_command
async def update_helper(
    ctx: Context,
    entity_id: str,
    name: str | None,
    icon: str | None,
    data: str | None,
) -> None:
    """Update a helper entity."""
    domain = entity_id.split(".")[0] if "." in entity_id else ""

    if domain not in HELPER_TYPES:
        from hab.exceptions import ValidationError
        raise ValidationError(f"Entity {entity_id} is not a helper entity")

    # Extract the object_id (part after the dot)
    object_id = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

    config = {}
    if name:
        config["name"] = name
    if icon:
        config["icon"] = icon
    if data:
        extra = json.loads(data)
        config.update(extra)

    if not config:
        from hab.exceptions import ValidationError
        raise ValidationError("No update parameters provided")

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command(
            f"{domain}/update",
            **{f"{domain}_id": object_id, **config},
        )

    print_output(result, text_mode=ctx.text_mode, message=f"Helper '{entity_id}' updated.")


@helper.command("delete")
@click.argument("entity_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_helper(ctx: Context, entity_id: str, force: bool) -> None:
    """Delete a helper entity."""
    domain = entity_id.split(".")[0] if "." in entity_id else ""

    if domain not in HELPER_TYPES:
        from hab.exceptions import ValidationError
        raise ValidationError(f"Entity {entity_id} is not a helper entity")

    if not force and not ctx.text_mode:
        click.confirm(f"Delete helper {entity_id}?", abort=True)

    # Extract the object_id (part after the dot)
    object_id = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command(f"{domain}/delete", **{f"{domain}_id": object_id})

    print_output(None, text_mode=ctx.text_mode, message=f"Helper '{entity_id}' deleted.")
