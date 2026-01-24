"""Action (service) commands."""

from __future__ import annotations

import json

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def action() -> None:
    """Call actions (services).

    List and call Home Assistant actions.
    """
    pass


@action.command("list")
@click.argument("domain", required=False)
@pass_context
@handle_errors
@async_command
async def list_actions(ctx: Context, domain: str | None) -> None:
    """List available actions.

    Optionally filter by DOMAIN (e.g., light, switch).
    """
    client = ctx.get_rest_client()
    async with client:
        services = await client.get_services()

    if domain:
        # Filter to specific domain
        services = [s for s in services if s.get("domain") == domain]

    # Flatten to list of actions
    actions = []
    for svc in services:
        svc_domain = svc.get("domain", "")
        for action_name, action_data in svc.get("services", {}).items():
            actions.append({
                "action": f"{svc_domain}.{action_name}",
                "name": action_data.get("name", action_name),
                "description": action_data.get("description", ""),
            })

    print_output(actions, text_mode=ctx.text_mode)


@action.command("call")
@click.argument("action_name")
@click.option("--data", "-d", help="Action data as JSON")
@click.option("--entity", "-e", "entity_id", help="Target entity ID")
@click.option("--area", "-a", "area_id", help="Target area ID")
@click.option("--return-response", "-r", is_flag=True, help="Return action response")
@pass_context
@handle_errors
@async_command
async def call_action(
    ctx: Context,
    action_name: str,
    data: str | None,
    entity_id: str | None,
    area_id: str | None,
    return_response: bool,
) -> None:
    """Call an action with data.

    ACTION_NAME should be in format domain.action (e.g., light.turn_on).
    """
    # Parse action name
    if "." not in action_name:
        from hab.exceptions import ValidationError
        raise ValidationError(
            f"Invalid action format: {action_name}. Expected domain.action"
        )

    domain, service = action_name.split(".", 1)

    # Parse data
    service_data = {}
    if data:
        service_data = json.loads(data)

    # Add target
    if entity_id:
        service_data["entity_id"] = entity_id
    if area_id:
        service_data["area_id"] = area_id

    client = ctx.get_rest_client()
    async with client:
        result = await client.call_service(
            domain,
            service,
            service_data,
            return_response=return_response,
        )

    if return_response and result:
        print_output(result, text_mode=ctx.text_mode)
    else:
        print_output(
            None,
            text_mode=ctx.text_mode,
            message=f"Action {action_name} called successfully.",
        )


@action.command("docs")
@click.argument("action_name")
@pass_context
@handle_errors
@async_command
async def action_docs(ctx: Context, action_name: str) -> None:
    """Show action documentation.

    ACTION_NAME should be in format domain.action (e.g., light.turn_on).
    """
    # Parse action name
    if "." not in action_name:
        from hab.exceptions import ValidationError
        raise ValidationError(
            f"Invalid action format: {action_name}. Expected domain.action"
        )

    domain, service = action_name.split(".", 1)

    client = ctx.get_rest_client()
    async with client:
        services = await client.get_services()

    # Find the specific service
    for svc in services:
        if svc.get("domain") == domain:
            service_data = svc.get("services", {}).get(service)
            if service_data:
                result = {
                    "action": action_name,
                    "name": service_data.get("name", service),
                    "description": service_data.get("description", ""),
                    "fields": service_data.get("fields", {}),
                    "target": service_data.get("target"),
                }
                print_output(result, text_mode=ctx.text_mode)
                return

    from hab.exceptions import ResourceNotFoundError
    raise ResourceNotFoundError(f"Action '{action_name}' not found")
