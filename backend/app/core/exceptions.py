"""Custom exceptions and exception handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    """Unauthorized access exception."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """Forbidden access exception."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, message: str = "Validation error", details: dict[str, Any] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )
