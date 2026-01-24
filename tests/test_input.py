"""Tests for input parsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hab.utils.input import parse_input, parse_key_value


class TestParseInput:
    """Tests for parse_input function."""

    def test_parse_json_string(self) -> None:
        """Test parsing JSON string."""
        data = '{"key": "value", "number": 42}'
        result = parse_input(data=data)

        assert result["key"] == "value"
        assert result["number"] == 42

    def test_parse_yaml_string(self) -> None:
        """Test parsing YAML string."""
        data = """
key: value
number: 42
list:
  - item1
  - item2
"""
        result = parse_input(data=data)

        assert result["key"] == "value"
        assert result["number"] == 42
        assert result["list"] == ["item1", "item2"]

    def test_parse_json_file(self, tmp_path: Path) -> None:
        """Test parsing JSON file."""
        file_path = tmp_path / "data.json"
        file_path.write_text('{"key": "value"}')

        result = parse_input(file=str(file_path))
        assert result["key"] == "value"

    def test_parse_yaml_file(self, tmp_path: Path) -> None:
        """Test parsing YAML file."""
        file_path = tmp_path / "data.yaml"
        file_path.write_text("key: value\nnumber: 42")

        result = parse_input(file=str(file_path))
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_force_json_format(self) -> None:
        """Test forcing JSON format."""
        data = '{"key": "value"}'
        result = parse_input(data=data, format="json")
        assert result["key"] == "value"

    def test_force_yaml_format(self) -> None:
        """Test forcing YAML format."""
        data = "key: value"
        result = parse_input(data=data, format="yaml")
        assert result["key"] == "value"

    def test_no_input_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when no input provided."""
        # Mock stdin to be a tty (no piped input)
        import io
        import sys

        class MockStdin:
            def isatty(self) -> bool:
                return True
            def read(self) -> str:
                return ""

        monkeypatch.setattr(sys, "stdin", MockStdin())

        with pytest.raises(ValueError, match="No input data provided"):
            parse_input()

    def test_empty_input_error(self) -> None:
        """Test error when input is empty."""
        with pytest.raises(ValueError, match="Input data is empty"):
            parse_input(data="   ")

    def test_file_not_found(self) -> None:
        """Test error when file not found."""
        with pytest.raises(ValueError, match="File not found"):
            parse_input(file="/nonexistent/file.json")


class TestParseKeyValue:
    """Tests for parse_key_value function."""

    def test_simple_values(self) -> None:
        """Test parsing simple key=value pairs."""
        result = parse_key_value(("name=test", "count=42"))

        assert result["name"] == "test"
        assert result["count"] == 42

    def test_json_values(self) -> None:
        """Test parsing JSON values."""
        result = parse_key_value(('data={"key": "value"}', "list=[1,2,3]"))

        assert result["data"] == {"key": "value"}
        assert result["list"] == [1, 2, 3]

    def test_boolean_values(self) -> None:
        """Test parsing boolean values."""
        result = parse_key_value(("enabled=true", "disabled=false"))

        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_invalid_format(self) -> None:
        """Test error on invalid format."""
        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_key_value(("invalid",))

    def test_value_with_equals(self) -> None:
        """Test value containing equals sign."""
        result = parse_key_value(("equation=a=b+c",))
        assert result["equation"] == "a=b+c"
