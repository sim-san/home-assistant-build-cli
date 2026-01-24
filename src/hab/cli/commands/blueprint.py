"""Blueprint commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def blueprint() -> None:
    """Manage blueprints.

    List and import blueprints.
    """
    pass


@blueprint.command("list")
@click.argument("domain", required=False, type=click.Choice(["automation", "script"]))
@pass_context
@handle_errors
@async_command
async def list_blueprints(ctx: Context, domain: str | None) -> None:
    """List blueprints.

    Optionally filter by DOMAIN (automation or script).
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("blueprint/list")

    blueprints = []
    for bp_domain, bp_list in result.items():
        if domain and bp_domain != domain:
            continue
        for path, bp_data in bp_list.items():
            blueprints.append({
                "domain": bp_domain,
                "path": path,
                "name": bp_data.get("metadata", {}).get("name", path),
                "description": bp_data.get("metadata", {}).get("description", ""),
            })

    print_output(blueprints, text_mode=ctx.text_mode)


@blueprint.command("import")
@click.argument("url")
@pass_context
@handle_errors
@async_command
async def import_blueprint(ctx: Context, url: str) -> None:
    """Import a blueprint from URL.

    URL should be a link to a blueprint YAML file or a Home Assistant
    community blueprint URL.
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("blueprint/import", url=url)

    print_output(result, text_mode=ctx.text_mode, message="Blueprint imported.")


@blueprint.command("get")
@click.argument("domain", type=click.Choice(["automation", "script"]))
@click.argument("path")
@pass_context
@handle_errors
@async_command
async def get_blueprint(ctx: Context, domain: str, path: str) -> None:
    """Get blueprint configuration.

    DOMAIN is either 'automation' or 'script'.
    PATH is the blueprint path (e.g., 'motion_light.yaml').
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("blueprint/list")

    bp_list = result.get(domain, {})
    if path not in bp_list:
        from hab.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(f"Blueprint '{path}' not found in {domain}")

    print_output(bp_list[path], text_mode=ctx.text_mode)
