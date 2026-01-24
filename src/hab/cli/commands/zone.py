"""Zone commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.input import parse_input
from hab.utils.output import print_output


@click.group()
def zone() -> None:
    """Manage zones.

    Create, update, and delete zones.
    """
    pass


@zone.command("list")
@pass_context
@handle_errors
@async_command
async def list_zones(ctx: Context) -> None:
    """List all zones."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    # Filter to zones
    zones = [
        s for s in states
        if s.get("entity_id", "").startswith("zone.")
    ]

    result = [
        {
            "entity_id": z["entity_id"],
            "name": z.get("attributes", {}).get("friendly_name", ""),
            "latitude": z.get("attributes", {}).get("latitude"),
            "longitude": z.get("attributes", {}).get("longitude"),
            "radius": z.get("attributes", {}).get("radius"),
            "icon": z.get("attributes", {}).get("icon"),
        }
        for z in zones
    ]

    print_output(result, text_mode=ctx.text_mode)


@zone.command("create")
@click.option("--name", "-n", required=True, help="Zone name")
@click.option("--latitude", "-lat", required=True, type=float, help="Latitude")
@click.option("--longitude", "-lon", required=True, type=float, help="Longitude")
@click.option("--radius", "-r", default=100.0, type=float, help="Radius in meters")
@click.option("--icon", help="Icon for the zone")
@click.option("--passive", is_flag=True, help="Make zone passive")
@pass_context
@handle_errors
@async_command
async def create_zone(
    ctx: Context,
    name: str,
    latitude: float,
    longitude: float,
    radius: float,
    icon: str | None,
    passive: bool,
) -> None:
    """Create a new zone."""
    kwargs = {}
    if icon:
        kwargs["icon"] = icon
    if passive:
        kwargs["passive"] = True

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.zone_create(
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            **kwargs,
        )

    print_output(result, text_mode=ctx.text_mode, message=f"Zone '{name}' created.")


@zone.command("update")
@click.argument("zone_id")
@click.option("--name", "-n", help="New name for the zone")
@click.option("--latitude", "-lat", type=float, help="Latitude")
@click.option("--longitude", "-lon", type=float, help="Longitude")
@click.option("--radius", "-r", type=float, help="Radius in meters")
@click.option("--icon", help="Icon for the zone")
@pass_context
@handle_errors
@async_command
async def update_zone(
    ctx: Context,
    zone_id: str,
    name: str | None,
    latitude: float | None,
    longitude: float | None,
    radius: float | None,
    icon: str | None,
) -> None:
    """Update a zone."""
    kwargs = {}
    if name:
        kwargs["name"] = name
    if latitude is not None:
        kwargs["latitude"] = latitude
    if longitude is not None:
        kwargs["longitude"] = longitude
    if radius is not None:
        kwargs["radius"] = radius
    if icon:
        kwargs["icon"] = icon

    if not kwargs:
        from hab.exceptions import ValidationError
        raise ValidationError("No update parameters provided")

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.zone_update(zone_id, **kwargs)

    print_output(result, text_mode=ctx.text_mode, message=f"Zone '{zone_id}' updated.")


@zone.command("delete")
@click.argument("zone_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_zone(ctx: Context, zone_id: str, force: bool) -> None:
    """Delete a zone."""
    if not force and not ctx.text_mode:
        click.confirm(f"Delete zone {zone_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.zone_delete(zone_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Zone '{zone_id}' deleted.")
