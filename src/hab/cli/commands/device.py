"""Device commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def device() -> None:
    """Device management.

    List and manage devices.
    """
    pass


@device.command("list")
@click.option("--area", "-a", help="Filter by area ID")
@click.option("--integration", "-i", help="Filter by integration")
@pass_context
@handle_errors
@async_command
async def list_devices(
    ctx: Context,
    area: str | None,
    integration: str | None,
) -> None:
    """List all devices."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        devices = await ws.device_registry_list()

    # Apply filters
    if area:
        devices = [d for d in devices if d.get("area_id") == area]

    # Format output
    result = [
        {
            "id": d.get("id"),
            "name": d.get("name") or d.get("name_by_user"),
            "manufacturer": d.get("manufacturer"),
            "model": d.get("model"),
            "area_id": d.get("area_id"),
            "disabled_by": d.get("disabled_by"),
            "labels": d.get("labels", []),
        }
        for d in devices
    ]

    print_output(result, text_mode=ctx.text_mode)


@device.command("get")
@click.argument("device_id")
@pass_context
@handle_errors
@async_command
async def get_device(ctx: Context, device_id: str) -> None:
    """Get device details.

    DEVICE_ID is the device identifier.
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        devices = await ws.device_registry_list()

    # Find the device
    device = next((d for d in devices if d.get("id") == device_id), None)

    if not device:
        from hab.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(f"Device '{device_id}' not found")

    print_output(device, text_mode=ctx.text_mode)


@device.command("delete")
@click.argument("device_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_device(ctx: Context, device_id: str, force: bool) -> None:
    """Delete a device.

    DEVICE_ID is the device identifier.
    """
    if not force and not ctx.text_mode:
        click.confirm(f"Delete device {device_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command("config/device_registry/remove_config_entry", device_id=device_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Device '{device_id}' deleted.")


@device.command("entities")
@click.argument("device_id")
@pass_context
@handle_errors
@async_command
async def device_entities(ctx: Context, device_id: str) -> None:
    """List entities for a device.

    DEVICE_ID is the device identifier.
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        entities = await ws.entity_registry_list()

    # Filter to this device
    device_entities = [
        {
            "entity_id": e.get("entity_id"),
            "name": e.get("name") or e.get("original_name"),
            "platform": e.get("platform"),
            "disabled_by": e.get("disabled_by"),
        }
        for e in entities
        if e.get("device_id") == device_id
    ]

    print_output(device_entities, text_mode=ctx.text_mode)
