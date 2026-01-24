"""Calendar commands."""

from __future__ import annotations

from datetime import datetime, timedelta

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.input import parse_input
from hab.utils.output import print_output


@click.group()
def calendar() -> None:
    """Manage calendar events.

    List, create, update, and delete calendar events.
    """
    pass


@calendar.command("list")
@click.argument("entity_id")
@click.option("--start", "-s", help="Start time (ISO format)")
@click.option("--end", "-e", help="End time (ISO format)")
@click.option("--days", "-d", type=int, default=7, help="Number of days to look ahead")
@pass_context
@handle_errors
@async_command
async def list_events(
    ctx: Context,
    entity_id: str,
    start: str | None,
    end: str | None,
    days: int,
) -> None:
    """List calendar events.

    ENTITY_ID is the calendar entity (e.g., calendar.home).
    """
    # Default to today + days
    if not start:
        start = datetime.now().isoformat()
    if not end:
        end = (datetime.now() + timedelta(days=days)).isoformat()

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command(
            "calendar/event/list",
            entity_id=entity_id,
            start=start,
            end=end,
        )

    events = result.get("events", [])
    formatted = [
        {
            "uid": e.get("uid"),
            "summary": e.get("summary"),
            "start": e.get("start"),
            "end": e.get("end"),
            "location": e.get("location"),
            "description": e.get("description"),
        }
        for e in events
    ]

    print_output(formatted, text_mode=ctx.text_mode)


@calendar.command("create")
@click.argument("entity_id")
@click.option("--summary", "-s", required=True, help="Event summary/title")
@click.option("--start", required=True, help="Start time (ISO format)")
@click.option("--end", required=True, help="End time (ISO format)")
@click.option("--description", "-d", help="Event description")
@click.option("--location", "-l", help="Event location")
@pass_context
@handle_errors
@async_command
async def create_event(
    ctx: Context,
    entity_id: str,
    summary: str,
    start: str,
    end: str,
    description: str | None,
    location: str | None,
) -> None:
    """Create a calendar event.

    ENTITY_ID is the calendar entity (e.g., calendar.home).
    """
    event_data = {
        "summary": summary,
        "start": start,
        "end": end,
    }
    if description:
        event_data["description"] = description
    if location:
        event_data["location"] = location

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command(
            "calendar/event/create",
            entity_id=entity_id,
            event=event_data,
        )

    print_output(result, text_mode=ctx.text_mode, message="Event created.")


@calendar.command("update")
@click.argument("entity_id")
@click.argument("uid")
@click.option("--summary", "-s", help="Event summary/title")
@click.option("--start", help="Start time (ISO format)")
@click.option("--end", help="End time (ISO format)")
@click.option("--description", "-d", help="Event description")
@click.option("--location", "-l", help="Event location")
@pass_context
@handle_errors
@async_command
async def update_event(
    ctx: Context,
    entity_id: str,
    uid: str,
    summary: str | None,
    start: str | None,
    end: str | None,
    description: str | None,
    location: str | None,
) -> None:
    """Update a calendar event.

    ENTITY_ID is the calendar entity.
    UID is the event unique identifier.
    """
    event_data = {"uid": uid}
    if summary:
        event_data["summary"] = summary
    if start:
        event_data["start"] = start
    if end:
        event_data["end"] = end
    if description:
        event_data["description"] = description
    if location:
        event_data["location"] = location

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command(
            "calendar/event/update",
            entity_id=entity_id,
            event=event_data,
        )

    print_output(result, text_mode=ctx.text_mode, message="Event updated.")


@calendar.command("delete")
@click.argument("entity_id")
@click.argument("uid")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_event(ctx: Context, entity_id: str, uid: str, force: bool) -> None:
    """Delete a calendar event.

    ENTITY_ID is the calendar entity.
    UID is the event unique identifier.
    """
    if not force and not ctx.text_mode:
        click.confirm(f"Delete event {uid}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command(
            "calendar/event/delete",
            entity_id=entity_id,
            uid=uid,
        )

    print_output(None, text_mode=ctx.text_mode, message="Event deleted.")
