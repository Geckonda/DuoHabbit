"""Typed domain errors, converted to HTTP responses by handlers registered in main.py."""


class AppError(Exception):
    """Base class for domain errors that should surface as a clean HTTP response."""

    status_code: int = 400


class NotFoundError(AppError):
    """Requested resource does not exist (or is not visible to the caller)."""

    status_code = 404


class ForbiddenError(AppError):
    """Caller is authenticated but not allowed to perform this action."""

    status_code = 403


class ConflictError(AppError):
    """Action conflicts with existing state (e.g. duplicate check-in)."""

    status_code = 409


class ValidationAppError(AppError):
    """Domain-level validation failure not already covered by Pydantic."""

    status_code = 400
