"""Script commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.input import parse_input
from hab.utils.output import print_output


@click.group()
def script() -> None:
    """Manage Home Assistant scripts.

    Create, update, delete, and run scripts.
    """
    pass


@script.command("list")
@pass_context
@handle_errors
@async_command
async def list_scripts(ctx: Context) -> None:
    """List all scripts."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    # Filter to scripts
    scripts = [
        s for s in states
        if s.get("entity_id", "").startswith("script.")
    ]

    # Extract relevant info
    result = [
        {
            "entity_id": s["entity_id"],
            "name": s.get("attributes", {}).get("friendly_name", ""),
            "state": s.get("state"),
            "last_triggered": s.get("attributes", {}).get("last_triggered"),
        }
        for s in scripts
    ]

    print_output(result, text_mode=ctx.text_mode)


@script.command("get")
@click.argument("script_id")
@pass_context
@handle_errors
@async_command
async def get_script(ctx: Context, script_id: str) -> None:
    """Get script configuration.

    SCRIPT_ID can be the entity_id (script.xxx) or just the script ID.
    """
    # Normalize ID
    if script_id.startswith("script."):
        script_id = script_id[7:]

    client = ctx.get_rest_client()
    async with client:
        config = await client.get(f"config/script/config/{script_id}")

    print_output(config, text_mode=ctx.text_mode)


@script.command("create")
@click.option("--data", "-d", help="Script configuration as JSON")
@click.option("--file", "-f", "file_path", type=click.Path(exists=True), help="Path to config file")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), help="Input format")
@pass_context
@handle_errors
@async_command
async def create_script(
    ctx: Context,
    data: str | None,
    file_path: str | None,
    fmt: str | None,
) -> None:
    """Create a new script from YAML/JSON."""
    config = parse_input(data=data, file=file_path, format=fmt)

    # Ensure required fields
    if "alias" not in config:
        from hab.exceptions import ValidationError
        raise ValidationError("Script must have an 'alias' field")

    client = ctx.get_rest_client()
    async with client:
        result = await client.post("config/script/config", config)

    print_output(result, text_mode=ctx.text_mode, message="Script created successfully.")


@script.command("update")
@click.argument("script_id")
@click.option("--data", "-d", help="Updated configuration as JSON")
@click.option("--file", "-f", "file_path", type=click.Path(exists=True), help="Path to config file")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), help="Input format")
@pass_context
@handle_errors
@async_command
async def update_script(
    ctx: Context,
    script_id: str,
    data: str | None,
    file_path: str | None,
    fmt: str | None,
) -> None:
    """Update an existing script."""
    config = parse_input(data=data, file=file_path, format=fmt)

    # Normalize ID
    if script_id.startswith("script."):
        script_id = script_id[7:]

    client = ctx.get_rest_client()
    async with client:
        result = await client.post(f"config/script/config/{script_id}", config)

    print_output(result, text_mode=ctx.text_mode, message="Script updated successfully.")


@script.command("delete")
@click.argument("script_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_script(ctx: Context, script_id: str, force: bool) -> None:
    """Delete a script."""
    # Normalize ID
    if script_id.startswith("script."):
        script_id = script_id[7:]

    if not force and not ctx.text_mode:
        click.confirm(f"Delete script {script_id}?", abort=True)

    client = ctx.get_rest_client()
    async with client:
        await client.delete(f"config/script/config/{script_id}")

    print_output(None, text_mode=ctx.text_mode, message=f"Script {script_id} deleted.")


@script.command("run")
@click.argument("script_id")
@click.option("--data", "-d", help="Variables to pass to script as JSON")
@pass_context
@handle_errors
@async_command
async def run_script(ctx: Context, script_id: str, data: str | None) -> None:
    """Execute a script."""
    # Normalize ID
    if not script_id.startswith("script."):
        script_id = f"script.{script_id}"

    service_data = {"entity_id": script_id}

    if data:
        import json
        variables = json.loads(data)
        service_data["variables"] = variables

    client = ctx.get_rest_client()
    async with client:
        await client.call_service("script", "turn_on", service_data)

    print_output(None, text_mode=ctx.text_mode, message=f"Script {script_id} executed.")
