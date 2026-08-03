"""
Custom Exception Classes — Consistent error handling across the application.
"""

from fastapi import HTTPException, status


class DataVisionException(Exception):
    """Base exception for all DataVision errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class AuthenticationError(DataVisionException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, error_code="AUTH_FAILED")


class AuthorizationError(DataVisionException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, error_code="FORBIDDEN")


class NotFoundError(DataVisionException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str = ""):
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(msg, error_code="NOT_FOUND")


class ConflictError(DataVisionException):
    """Raised when a resource already exists."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, error_code="CONFLICT")


class ValidationError(DataVisionException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, error_code="VALIDATION_ERROR")


class RateLimitError(DataVisionException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, error_code="RATE_LIMIT")


def to_http_exception(exc: DataVisionException) -> HTTPException:
    """Convert a DataVisionException to an HTTPException."""
    status_map = {
        "AUTH_FAILED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "RATE_LIMIT": status.HTTP_429_TOO_MANY_REQUESTS,
        "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    return HTTPException(
        status_code=status_map.get(exc.error_code, 500),
        detail=exc.message,
    )
