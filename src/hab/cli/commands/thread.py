"""Thread commands."""

from __future__ import annotations

import click

from hab.cli.main import Context, async_command, handle_errors, pass_context
from hab.utils.output import print_output


@click.group()
def thread() -> None:
    """Manage Thread credentials.

    List, add, and manage Thread network datasets.
    """
    pass


@thread.command("list")
@pass_context
@handle_errors
@async_command
async def list_datasets(ctx: Context) -> None:
    """List all Thread datasets."""
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("thread/list_datasets")

    datasets = result.get("datasets", [])
    formatted = [
        {
            "dataset_id": d.get("dataset_id"),
            "preferred": d.get("preferred", False),
            "network_name": d.get("network_name"),
            "extended_pan_id": d.get("extended_pan_id"),
            "channel": d.get("channel"),
        }
        for d in datasets
    ]

    print_output(formatted, text_mode=ctx.text_mode)


@thread.command("get")
@click.argument("dataset_id")
@pass_context
@handle_errors
@async_command
async def get_dataset(ctx: Context, dataset_id: str) -> None:
    """Get dataset details including TLV.

    DATASET_ID is the dataset identifier.
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("thread/get_dataset", dataset_id=dataset_id)

    print_output(result, text_mode=ctx.text_mode)


@thread.command("add")
@click.argument("tlv")
@pass_context
@handle_errors
@async_command
async def add_dataset(ctx: Context, tlv: str) -> None:
    """Add a new Thread dataset from TLV.

    TLV is the Thread operational dataset in TLV format (hex string).
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("thread/add_dataset_tlv", tlv=tlv)

    print_output(result, text_mode=ctx.text_mode, message="Thread dataset added.")


@thread.command("delete")
@click.argument("dataset_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@pass_context
@handle_errors
@async_command
async def delete_dataset(ctx: Context, dataset_id: str, force: bool) -> None:
    """Delete a Thread dataset.

    DATASET_ID is the dataset identifier.
    """
    if not force and not ctx.text_mode:
        click.confirm(f"Delete Thread dataset {dataset_id}?", abort=True)

    async with ctx.get_ws_client() as ws:
        await ws.connect()
        await ws.send_command("thread/delete_dataset", dataset_id=dataset_id)

    print_output(None, text_mode=ctx.text_mode, message=f"Thread dataset '{dataset_id}' deleted.")


@thread.command("set-preferred")
@click.argument("dataset_id")
@pass_context
@handle_errors
@async_command
async def set_preferred(ctx: Context, dataset_id: str) -> None:
    """Set a dataset as the preferred network.

    DATASET_ID is the dataset identifier.
    """
    async with ctx.get_ws_client() as ws:
        await ws.connect()
        result = await ws.send_command("thread/set_preferred_dataset", dataset_id=dataset_id)

    print_output(result, text_mode=ctx.text_mode, message=f"Dataset '{dataset_id}' set as preferred.")
