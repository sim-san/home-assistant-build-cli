"""Entity commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def entity() -> None:
    """Entity operations.

    List, get, search, and manage entities.
    """
    pass


@entity.command("list")
@click.option("--domain", "-d", help="Filter by domain (e.g., light, switch)")
@click.option("--area", "-a", help="Filter by area ID")
@click.option("--label", "-l", help="Filter by label ID")
@pass_context
@handle_errors
@async_command
async def list_entities(
    ctx: Context,
    domain: str | None,
    area: str | None,
    label: str | None,
) -> None:
    """List entities with optional filtering."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()

        # Get entity registry for additional info
        registry = await ws.entity_registry_list()
        registry_map = {e["entity_id"]: e for e in registry}

        # Get states
        states = await ws.get_states()

    # Combine state with registry info
    entities = []
    for state in states:
        entity_id = state.get("entity_id", "")
        entity_domain = entity_id.split(".")[0] if "." in entity_id else ""

        # Apply domain filter
        if domain and entity_domain != domain:
            continue

        reg_entry = registry_map.get(entity_id, {})

        # Apply area filter
        if area and reg_entry.get("area_id") != area:
            continue

        # Apply label filter
        if label and label not in reg_entry.get("labels", []):
            continue

        entities.append({
            "entity_id": entity_id,
            "state": state.get("state"),
            "name": state.get("attributes", {}).get("friendly_name", ""),
            "area_id": reg_entry.get("area_id"),
            "labels": reg_entry.get("labels", []),
            "disabled": reg_entry.get("disabled_by") is not None,
        })

    print_output(entities, text_mode=ctx.text_mode)


@entity.command("get")
@click.argument("entity_id")
@pass_context
@handle_errors
@async_command
async def get_entity(ctx: Context, entity_id: str) -> None:
    """Get entity state and attributes."""
    client = ctx.get_rest_client()
    async with client:
        state = await client.get_state(entity_id)

    print_output(state, text_mode=ctx.text_mode)


@entity.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=10, help="Maximum number of results")
@pass_context
@handle_errors
@async_command
async def search_entities(ctx: Context, query: str, limit: int) -> None:
    """Fuzzy search for entities."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    query_lower = query.lower()

    # Simple fuzzy matching
    matches = []
    for state in states:
        entity_id = state.get("entity_id", "")
        friendly_name = state.get("attributes", {}).get("friendly_name", "")

        # Check if query matches entity_id or friendly_name
        score = 0
        if query_lower in entity_id.lower():
            score = 100 - len(entity_id)  # Prefer shorter matches
        elif query_lower in friendly_name.lower():
            score = 50 - len(friendly_name)

        if score > 0:
            matches.append({
                "entity_id": entity_id,
                "name": friendly_name,
                "state": state.get("state"),
                "score": score,
            })

    # Sort by score and limit
    matches.sort(key=lambda x: x["score"], reverse=True)
    matches = matches[:limit]

    # Remove score from output
    for m in matches:
        del m["score"]

    print_output(matches, text_mode=ctx.text_mode)


@entity.command("history")
@click.argument("entity_id")
@click.option("--start", "-s", help="Start time (ISO format)")
@click.option("--end", "-e", help="End time (ISO format)")
@pass_context
@handle_errors
@async_command
async def entity_history(
    ctx: Context,
    entity_id: str,
    start: str | None,
    end: str | None,
) -> None:
    """Get state history for an entity."""
    client = ctx.get_rest_client()
    async with client:
        history = await client.get_history(
            entity_id=entity_id,
            start_time=start,
            end_time=end,
        )

    # Flatten the nested list
    if history and len(history) > 0:
        print_output(history[0], text_mode=ctx.text_mode)
    else:
        print_output([], text_mode=ctx.text_mode)


@entity.command("rename")
@click.argument("entity_id")
@click.argument("new_name")
@pass_context
@handle_errors
@async_command
async def rename_entity(ctx: Context, entity_id: str, new_name: str) -> None:
    """Rename an entity."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.entity_registry_update(entity_id, name=new_name)

    print_output(result, text_mode=ctx.text_mode, message=f"Entity renamed to {new_name}.")


@entity.command("enable")
@click.argument("entity_id")
@pass_context
@handle_errors
@async_command
async def enable_entity(ctx: Context, entity_id: str) -> None:
    """Enable a disabled entity."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.entity_registry_update(entity_id, disabled_by=None)

    print_output(result, text_mode=ctx.text_mode, message=f"Entity {entity_id} enabled.")


@entity.command("disable")
@click.argument("entity_id")
@pass_context
@handle_errors
@async_command
async def disable_entity(ctx: Context, entity_id: str) -> None:
    """Disable an entity."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.entity_registry_update(entity_id, disabled_by="user")

    print_output(result, text_mode=ctx.text_mode, message=f"Entity {entity_id} disabled.")
