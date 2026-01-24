"""Output formatting utilities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()
error_console = Console(stderr=True)


def format_output(
    data: Any,
    *,
    text_mode: bool = False,
    success: bool = True,
    message: str | None = None,
) -> str:
    """Format output data.

    Args:
        data: Data to format.
        text_mode: Use human-readable text format instead of JSON.
        success: Whether the operation was successful.
        message: Optional message to include.

    Returns:
        Formatted output string.
    """
    if text_mode:
        return _format_text(data, message)

    output = {
        "success": success,
        "data": data,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    }
    if message:
        output["message"] = message

    return json.dumps(output, indent=2, default=str)


def format_error(
    error: Exception | str,
    *,
    text_mode: bool = False,
    code: str = "GENERAL_ERROR",
    details: dict[str, Any] | None = None,
    suggestion: str | None = None,
) -> str:
    """Format error output.

    Args:
        error: Error exception or message.
        text_mode: Use human-readable text format instead of JSON.
        code: Error code.
        details: Additional error details.
        suggestion: Suggested action to fix the error.

    Returns:
        Formatted error string.
    """
    message = str(error)

    if text_mode:
        output = f"Error: {message}"
        if suggestion:
            output += f"\nSuggestion: {suggestion}"
        return output

    error_data: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details:
        error_data["details"] = details
    if suggestion:
        error_data["details"] = error_data.get("details", {})
        error_data["details"]["suggestion"] = suggestion

    return json.dumps({"success": False, "error": error_data}, indent=2)


def _format_text(data: Any, message: str | None = None) -> str:
    """Format data as human-readable text.

    Args:
        data: Data to format.
        message: Optional message to include.

    Returns:
        Formatted text.
    """
    if message:
        return message

    if data is None:
        return "Done."

    if isinstance(data, str):
        return data

    if isinstance(data, bool):
        return "Yes" if data else "No"

    if isinstance(data, (int, float)):
        return str(data)

    if isinstance(data, list):
        return _format_list(data)

    if isinstance(data, dict):
        return _format_dict(data)

    return str(data)


def _format_list(data: list) -> str:
    """Format a list as text.

    Args:
        data: List to format.

    Returns:
        Formatted text.
    """
    if not data:
        return "No items."

    # If list of dicts with common keys, format as table
    if all(isinstance(item, dict) for item in data):
        return _format_dict_list(data)

    # Simple list
    lines = []
    for item in data:
        if isinstance(item, dict):
            # Extract meaningful identifier
            name = item.get("friendly_name") or item.get("name") or item.get("entity_id") or str(item)
            lines.append(f"  - {name}")
        else:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def _format_dict_list(data: list[dict]) -> str:
    """Format a list of dicts as a table.

    Args:
        data: List of dicts to format.

    Returns:
        Formatted text.
    """
    if not data:
        return "No items."

    # Get common keys (limit to first 6 for readability)
    keys = list(data[0].keys())[:6]

    lines = []

    # Header
    header = " | ".join(str(k).replace("_", " ").title() for k in keys)
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for item in data[:50]:  # Limit to 50 rows
        values = []
        for k in keys:
            v = item.get(k, "")
            if isinstance(v, (dict, list)):
                v = "..."
            values.append(str(v)[:30])
        lines.append(" | ".join(values))

    if len(data) > 50:
        lines.append(f"... and {len(data) - 50} more items")

    return "\n".join(lines)


def _format_dict(data: dict) -> str:
    """Format a dict as text.

    Args:
        data: Dict to format.

    Returns:
        Formatted text.
    """
    lines = []

    for key, value in data.items():
        key_label = str(key).replace("_", " ").title()

        if isinstance(value, dict):
            lines.append(f"{key_label}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"{key_label}:")
            for item in value[:10]:
                if isinstance(item, dict):
                    lines.append(f"  - {item.get('name', item.get('entity_id', item))}")
                else:
                    lines.append(f"  - {item}")
            if len(value) > 10:
                lines.append(f"  ... and {len(value) - 10} more")
        else:
            lines.append(f"{key_label}: {value}")

    return "\n".join(lines)


def print_output(
    data: Any,
    *,
    text_mode: bool = False,
    success: bool = True,
    message: str | None = None,
) -> None:
    """Print formatted output to stdout.

    Args:
        data: Data to output.
        text_mode: Use human-readable text format.
        success: Whether the operation was successful.
        message: Optional message to include.
    """
    output = format_output(data, text_mode=text_mode, success=success, message=message)
    console.print(output, highlight=False)


def print_error(
    error: Exception | str,
    *,
    text_mode: bool = False,
    code: str = "GENERAL_ERROR",
    details: dict[str, Any] | None = None,
    suggestion: str | None = None,
) -> None:
    """Print formatted error to stderr.

    Args:
        error: Error exception or message.
        text_mode: Use human-readable text format.
        code: Error code.
        details: Additional error details.
        suggestion: Suggested action to fix the error.
    """
    output = format_error(
        error,
        text_mode=text_mode,
        code=code,
        details=details,
        suggestion=suggestion,
    )
    error_console.print(output, highlight=False)
