"""Custom exceptions for hab CLI."""

from enum import IntEnum


class ExitCode(IntEnum):
    """CLI exit codes."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    AUTHENTICATION_ERROR = 3
    RESOURCE_NOT_FOUND = 4
    PERMISSION_DENIED = 5
    CONNECTION_ERROR = 6
    VALIDATION_ERROR = 7
    TIMEOUT = 8


class HabError(Exception):
    """Base exception for hab CLI."""

    exit_code: ExitCode = ExitCode.GENERAL_ERROR
    error_code: str = "GENERAL_ERROR"

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(HabError):
    """Authentication failed."""

    exit_code = ExitCode.AUTHENTICATION_ERROR
    error_code = "AUTHENTICATION_ERROR"


class ConnectionError(HabError):
    """Connection to Home Assistant failed."""

    exit_code = ExitCode.CONNECTION_ERROR
    error_code = "CONNECTION_ERROR"


class ResourceNotFoundError(HabError):
    """Requested resource was not found."""

    exit_code = ExitCode.RESOURCE_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"


class ValidationError(HabError):
    """Input validation failed."""

    exit_code = ExitCode.VALIDATION_ERROR
    error_code = "VALIDATION_ERROR"


class PermissionError(HabError):
    """Permission denied for operation."""

    exit_code = ExitCode.PERMISSION_DENIED
    error_code = "PERMISSION_DENIED"


class TimeoutError(HabError):
    """Operation timed out."""

    exit_code = ExitCode.TIMEOUT
    error_code = "TIMEOUT"
