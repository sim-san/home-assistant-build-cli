"""Tests for output formatting."""

from __future__ import annotations

import json

import pytest

from hab.utils.output import format_error, format_output


class TestFormatOutput:
    """Tests for format_output function."""

    def test_json_output_simple(self) -> None:
        """Test simple JSON output."""
        result = format_output({"key": "value"})
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["data"] == {"key": "value"}
        assert "timestamp" in parsed["metadata"]

    def test_json_output_with_message(self) -> None:
        """Test JSON output with message."""
        result = format_output({"key": "value"}, message="Operation completed")
        parsed = json.loads(result)

        assert parsed["message"] == "Operation completed"

    def test_json_output_failure(self) -> None:
        """Test JSON output for failure."""
        result = format_output(None, success=False)
        parsed = json.loads(result)

        assert parsed["success"] is False

    def test_text_output_string(self) -> None:
        """Test text output with string data."""
        result = format_output("Hello, World!", text_mode=True)
        assert result == "Hello, World!"

    def test_text_output_dict(self) -> None:
        """Test text output with dict data."""
        result = format_output(
            {"name": "Test", "value": 42},
            text_mode=True,
        )
        assert "Name: Test" in result
        assert "Value: 42" in result

    def test_text_output_list(self) -> None:
        """Test text output with list data."""
        result = format_output(
            [{"entity_id": "light.test"}, {"entity_id": "switch.test"}],
            text_mode=True,
        )
        assert "light.test" in result or "Entity Id" in result

    def test_text_output_with_message(self) -> None:
        """Test text output with message."""
        result = format_output({"key": "value"}, text_mode=True, message="Done")
        assert result == "Done"


class TestFormatError:
    """Tests for format_error function."""

    def test_json_error(self) -> None:
        """Test JSON error output."""
        result = format_error("Something went wrong", code="TEST_ERROR")
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert parsed["error"]["code"] == "TEST_ERROR"
        assert parsed["error"]["message"] == "Something went wrong"

    def test_json_error_with_details(self) -> None:
        """Test JSON error with details."""
        result = format_error(
            "Not found",
            code="NOT_FOUND",
            details={"entity_id": "light.test"},
        )
        parsed = json.loads(result)

        assert parsed["error"]["details"]["entity_id"] == "light.test"

    def test_json_error_with_suggestion(self) -> None:
        """Test JSON error with suggestion."""
        result = format_error(
            "Not found",
            code="NOT_FOUND",
            suggestion="Check the entity ID",
        )
        parsed = json.loads(result)

        assert parsed["error"]["details"]["suggestion"] == "Check the entity ID"

    def test_text_error(self) -> None:
        """Test text error output."""
        result = format_error("Something went wrong", text_mode=True)
        assert "Error: Something went wrong" in result

    def test_text_error_with_suggestion(self) -> None:
        """Test text error with suggestion."""
        result = format_error(
            "Not found",
            text_mode=True,
            suggestion="Check the entity ID",
        )
        assert "Suggestion: Check the entity ID" in result
