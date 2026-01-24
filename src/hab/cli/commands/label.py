"""Label commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def label() -> None:
    """Manage labels.

    Create, update, delete, and assign labels.
    """
    pass


@label.command("list")
@pass_context
@handle_errors
@async_command
async def list_labels(ctx: Context) -> None:
    """List all labels."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        labels = await ws.label_registry_list()

    result = [
        {
            "label_id": l["label_id"],
            "name": l["name"],
            "icon": l.get("icon"),
            "color": l.get("color"),
            "description": l.get("description"),
        }
        for l in labels
    ]

    print_output(result, text_mode=ctx.text_mode)


@label.command("create")
@click.argument("name")
@click.option("--icon", help="Icon for the label")
@click.option("--color", help="Color for the label (hex)")
@click.option("--description", help="Description of the label")
@pass_context
@handle_errors
@async_command
async def create_label(
    ctx: Context,
    name: str,
    icon: str | None,
    color: str | None,
    description: str | None,
) -> None:
    """Create a new label."""
    kwargs = {}
    if icon:
        kwargs["icon"] = icon
    if color:
        kwargs["color"] = color
    if description:
        kwargs["description"] = description

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.label_registry_create(name, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Label '{name}' created.")


@label.command("update")
@click.argument("label_id")
@click.option("--name", help="New name for the label")
@click.option("--icon", help="Icon for the label")
@click.option("--color", help="Color for the label (hex)")
@click.option("--description", help="Description of the label")
@pass_context
@handle_errors
@async_command
async def update_label(
    ctx: Context,
    label_id: str,
    name: str | None,
    icon: str | None,
    color: str | None,
    description: str | None,
) -> None:
    """Update a label."""
    kwargs = {}
    if name:
        kwargs["name"] = name
    if icon:
        kwargs["icon"] = icon
    if color:
        kwargs["color"] = color
    if description:
        kwargs["description"] = description

    if not kwargs:
        from hab.exceptions import ValidationError
        raise ValidationError("No update parameters provided")

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.label_registry_update(label_id, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Label '{label_id}' updated.")


@label.command("delete")
@click.argument("label_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_label(ctx: Context, label_id: str, force: bool) -> None:
    """Delete a label."""
    if not force and not ctx.text_mode:
        click.confirm(f"Delete label {label_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.label_registry_delete(label_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Label '{label_id}' deleted.")


@label.command("assign")
@click.argument("label_id")
@click.argument("entity_id")
@pass_context
@handle_errors
@async_command
async def assign_label(ctx: Context, label_id: str, entity_id: str) -> None:
    """Assign a label to an entity."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()

        # Get current labels
        entity = await ws.entity_registry_get(entity_id)
        current_labels = entity.get("labels", [])

        if label_id in current_labels:
            print_output(
                entity,
                text_mode=ctx.text_mode,
                message=f"Label '{label_id}' already assigned to {entity_id}.",
            )
            return

        # Add the new label
        new_labels = current_labels + [label_id]
        result = await ws.entity_registry_update(entity_id, labels=new_labels)

    print_output(
        result,
        text_mode=ctx.text_mode,
        message=f"Label '{label_id}' assigned to {entity_id}.",
    )


@label.command("remove")
@click.argument("label_id")
@click.argument("entity_id")
@pass_context
@handle_errors
@async_command
async def remove_label(ctx: Context, label_id: str, entity_id: str) -> None:
    """Remove a label from an entity."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()

        # Get current labels
        entity = await ws.entity_registry_get(entity_id)
        current_labels = entity.get("labels", [])

        if label_id not in current_labels:
            print_output(
                entity,
                text_mode=ctx.text_mode,
                message=f"Label '{label_id}' not assigned to {entity_id}.",
            )
            return

        # Remove the label
        new_labels = [l for l in current_labels if l != label_id]
        result = await ws.entity_registry_update(entity_id, labels=new_labels)

    print_output(
        result,
        text_mode=ctx.text_mode,
        message=f"Label '{label_id}' removed from {entity_id}.",
    )
