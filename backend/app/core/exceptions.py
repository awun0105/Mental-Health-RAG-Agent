from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} with id '{resource_id}' was not found",
            status_code=404,
        )


class AlreadyExistsError(AppException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} '{identifier}' already exists",
            status_code=409,
        )


class UnauthorizedError(AppException):
    """Raised when authentication is missing or invalid."""

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenError(AppException):
    """Raised when the user is authenticated but not allowed to perform an action."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403)


class InvalidCredentialsError(AppException):
    """Raised when email/password login fails."""

    def __init__(self) -> None:
        super().__init__(message="Invalid email or password", status_code=401)


class ConsentRequiredError(AppException):
    """Raised when user has not accepted the current consent policy."""

    def __init__(self) -> None:
        super().__init__(
            message="Consent acceptance required before using the platform",
            status_code=403,
        )


class DatabaseError(AppException):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(message=message, status_code=500)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Convert AppException instances into consistent JSON API responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": exc.__class__.__name__,
        },
    )
