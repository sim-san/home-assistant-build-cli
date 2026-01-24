"""Automation commands."""

from __future__ import annotations

from typing import Any

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.input import parse_input
from hab.utils.output import print_output


@click.group()
def automation() -> None:
    """Manage Home Assistant automations.

    Create, update, delete, and trigger automations.
    """
    pass


@automation.command("list")
@click.option("--domain", help="Filter by entity domain")
@pass_context
@handle_errors
@async_command
async def list_automations(ctx: Context, domain: str | None) -> None:
    """List all automations."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        states = await ws.get_states()

    # Filter to automations
    automations = [
        s for s in states
        if s.get("entity_id", "").startswith("automation.")
    ]

    # Extract relevant info
    result = [
        {
            "entity_id": a["entity_id"],
            "alias": a.get("attributes", {}).get("friendly_name", ""),
            "state": a.get("state"),
            "last_triggered": a.get("attributes", {}).get("last_triggered"),
        }
        for a in automations
    ]

    print_output(result, text_mode=ctx.text_mode)


@automation.command("get")
@click.argument("automation_id")
@pass_context
@handle_errors
@async_command
async def get_automation(ctx: Context, automation_id: str) -> None:
    """Get automation configuration by ID.

    AUTOMATION_ID can be the entity_id (automation.xxx) or just the automation ID.
    """
    # Normalize ID
    if not automation_id.startswith("automation."):
        automation_id = f"automation.{automation_id}"

    client = ctx.get_rest_client()
    async with client:
        # Get the config
        config = await client.get(f"config/automation/config/{automation_id}")

    print_output(config, text_mode=ctx.text_mode)


@automation.command("create")
@click.option("--data", "-d", help="Automation configuration as JSON")
@click.option("--file", "-f", "file_path", type=click.Path(exists=True), help="Path to config file")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), help="Input format")
@pass_context
@handle_errors
@async_command
async def create_automation(
    ctx: Context,
    data: str | None,
    file_path: str | None,
    fmt: str | None,
) -> None:
    """Create a new automation from YAML/JSON."""
    config = parse_input(data=data, file=file_path, format=fmt)

    # Ensure required fields
    if "alias" not in config:
        from hab.exceptions import ValidationError
        raise ValidationError("Automation must have an 'alias' field")

    client = ctx.get_rest_client()
    async with client:
        result = await client.post("config/automation/config", config)

    print_output(result, text_mode=ctx.text_mode, message="Automation created successfully.")


@automation.command("update")
@click.argument("automation_id")
@click.option("--data", "-d", help="Updated configuration as JSON")
@click.option("--file", "-f", "file_path", type=click.Path(exists=True), help="Path to config file")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), help="Input format")
@pass_context
@handle_errors
@async_command
async def update_automation(
    ctx: Context,
    automation_id: str,
    data: str | None,
    file_path: str | None,
    fmt: str | None,
) -> None:
    """Update an existing automation."""
    config = parse_input(data=data, file=file_path, format=fmt)

    # Normalize ID
    if not automation_id.startswith("automation."):
        automation_id = f"automation.{automation_id}"

    client = ctx.get_rest_client()
    async with client:
        result = await client.post(f"config/automation/config/{automation_id}", config)

    print_output(result, text_mode=ctx.text_mode, message="Automation updated successfully.")


@automation.command("delete")
@click.argument("automation_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_automation(ctx: Context, automation_id: str, force: bool) -> None:
    """Delete an automation."""
    # Normalize ID
    if not automation_id.startswith("automation."):
        automation_id = f"automation.{automation_id}"

    if not force and not ctx.text_mode:
        click.confirm(f"Delete automation {automation_id}?", abort=True)

    client = ctx.get_rest_client()
    async with client:
        await client.delete(f"config/automation/config/{automation_id}")

    print_output(None, text_mode=ctx.text_mode, message=f"Automation {automation_id} deleted.")


@automation.command("trigger")
@click.argument("automation_id")
@click.option("--skip-condition", is_flag=True, help="Skip automation conditions")
@pass_context
@handle_errors
@async_command
async def trigger_automation(ctx: Context, automation_id: str, skip_condition: bool) -> None:
    """Manually trigger an automation."""
    # Normalize ID
    if not automation_id.startswith("automation."):
        automation_id = f"automation.{automation_id}"

    service_data: dict[str, Any] = {"entity_id": automation_id}
    if skip_condition:
        service_data["skip_condition"] = True

    client = ctx.get_rest_client()
    async with client:
        await client.call_service("automation", "trigger", service_data)

    print_output(None, text_mode=ctx.text_mode, message=f"Automation {automation_id} triggered.")


@automation.command("trace")
@click.argument("automation_id")
@click.option("--run-id", help="Specific run ID to get trace for")
@pass_context
@handle_errors
@async_command
async def trace_automation(ctx: Context, automation_id: str, run_id: str | None) -> None:
    """Get execution traces for debugging."""
    # Normalize ID
    if not automation_id.startswith("automation."):
        automation_id = f"automation.{automation_id}"

    async with ctx.get_ws_client() as ws:
        await ws.connect()

        if run_id:
            # Get specific trace
            trace = await ws.send_command(
                "trace/get",
                domain="automation",
                item_id=automation_id.replace("automation.", ""),
                run_id=run_id,
            )
            print_output(trace, text_mode=ctx.text_mode)
        else:
            # List traces
            traces = await ws.send_command(
                "trace/list",
                domain="automation",
                item_id=automation_id.replace("automation.", ""),
            )
            print_output(traces, text_mode=ctx.text_mode)
