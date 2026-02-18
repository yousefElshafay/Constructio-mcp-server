from __future__ import annotations
from typing import Any


class AppError(Exception):
    """Base category for application-specific errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundException(AppError):
    """Raised when a resource is not found."""

    pass


class ValidationException(AppError):
    """Raised when data validation fails."""

    pass
