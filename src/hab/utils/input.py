"""Input parsing utilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


def parse_input(
    data: str | None = None,
    file: str | None = None,
    format: str | None = None,
) -> dict[str, Any]:
    """Parse input data from various sources.

    Args:
        data: Inline JSON/YAML data string.
        file: Path to a file containing data.
        format: Force input format ('json' or 'yaml').

    Returns:
        Parsed data as a dictionary.

    Raises:
        ValueError: If input cannot be parsed.
    """
    content: str | None = None

    if data:
        content = data
    elif file:
        path = Path(file).expanduser()
        if not path.exists():
            raise ValueError(f"File not found: {file}")
        content = path.read_text()
        # Auto-detect format from extension if not specified
        if not format:
            if path.suffix.lower() in (".yaml", ".yml"):
                format = "yaml"
            elif path.suffix.lower() == ".json":
                format = "json"
    elif not sys.stdin.isatty():
        # Read from piped input
        content = sys.stdin.read()

    if not content:
        raise ValueError("No input data provided. Use --data, --file, or pipe input.")

    content = content.strip()

    if not content:
        raise ValueError("Input data is empty.")

    # Try to parse
    if format == "yaml" or (not format and not content.startswith("{")):
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            if format == "yaml":
                raise ValueError(f"Invalid YAML: {e}")
            # Fall through to try JSON

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        if format == "json":
            raise ValueError(f"Invalid JSON: {e}")
        # Try YAML as fallback
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            raise ValueError(f"Could not parse input as JSON or YAML: {e}")


def parse_key_value(args: tuple[str, ...]) -> dict[str, Any]:
    """Parse key=value arguments.

    Args:
        args: Tuple of key=value strings.

    Returns:
        Dictionary of parsed values.
    """
    result: dict[str, Any] = {}

    for arg in args:
        if "=" not in arg:
            raise ValueError(f"Invalid argument format: {arg}. Expected key=value.")

        key, value = arg.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Try to parse value as JSON for complex types
        try:
            result[key] = json.loads(value)
        except json.JSONDecodeError:
            # Keep as string
            result[key] = value

    return result
