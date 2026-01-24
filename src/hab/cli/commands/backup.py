"""Backup commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def backup() -> None:
    """Backup and restore.

    Create, list, and manage backups.
    """
    pass


@backup.command("list")
@pass_context
@handle_errors
@async_command
async def list_backups(ctx: Context) -> None:
    """List available backups."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("backup/info")

    backups = result.get("backups", [])
    formatted = [
        {
            "slug": b.get("slug"),
            "name": b.get("name"),
            "date": b.get("date"),
            "size": b.get("size"),
            "protected": b.get("protected", False),
        }
        for b in backups
    ]

    print_output(formatted, text_mode=ctx.text_mode)


@backup.command("create")
@click.argument("name", required=False)
@pass_context
@handle_errors
@async_command
async def create_backup(ctx: Context, name: str | None) -> None:
    """Create a new backup.

    NAME is optional; if not provided, a default name will be used.
    """
    kwargs = {}
    if name:
        kwargs["name"] = name

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("backup/generate", **kwargs)

    print_output(result, text_mode=ctx.text_mode, message="Backup creation started.")


@backup.command("restore")
@click.argument("slug")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def restore_backup(ctx: Context, slug: str, force: bool) -> None:
    """Restore from a backup.

    SLUG is the backup identifier from 'hab backup list'.
    """
    if not force:
        click.confirm(
            "This will restore Home Assistant from backup. Continue?",
            abort=True,
        )

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("backup/restore/full", slug=slug)

    print_output(result, text_mode=ctx.text_mode, message="Restore started.")


@backup.command("download")
@click.argument("slug")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@pass_context
@handle_errors
@async_command
async def download_backup(ctx: Context, slug: str, output: str | None) -> None:
    """Download a backup file.

    SLUG is the backup identifier from 'hab backup list'.
    """
    # Get download URL
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("auth/sign_path", path=f"/api/backup/download/{slug}")

    download_path = result.get("path")
    if not download_path:
        from hab.exceptions import ValidationError
        raise ValidationError("Failed to get download URL")

    # Download the file
    import httpx

    url = f"{ctx.auth.url}{download_path}"
    output_file = output or f"backup_{slug}.tar"

    async with httpx.AsyncClient(verify=ctx.settings.verify_ssl) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(output_file, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

    print_output(
        {"file": output_file},
        text_mode=ctx.text_mode,
        message=f"Backup downloaded to {output_file}",
    )


@backup.command("delete")
@click.argument("slug")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_backup(ctx: Context, slug: str, force: bool) -> None:
    """Delete a backup.

    SLUG is the backup identifier from 'hab backup list'.
    """
    if not force and not ctx.text_mode:
        click.confirm(f"Delete backup {slug}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command("backup/remove", slug=slug)

    print_output(None, text_mode=ctx.text_mode, message=f"Backup '{slug}' deleted.")
