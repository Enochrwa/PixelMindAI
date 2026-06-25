"""Custom exceptions and error handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class PixelMindError(Exception):
    """Base exception for PixelMind AI."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class AuthError(PixelMindError):
    """Authentication / authorization error."""

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message, "AUTH_ERROR")


class NotFoundError(PixelMindError):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} '{resource_id}' not found", "NOT_FOUND")


class ValidationError(PixelMindError):
    """Payload validation error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR")


class RateLimitError(PixelMindError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded", "RATE_LIMIT_EXCEEDED")


class InsufficientCreditsError(PixelMindError):
    """User has insufficient credits."""

    def __init__(self) -> None:
        super().__init__("Insufficient credits", "INSUFFICIENT_CREDITS")


class FileValidationError(PixelMindError):
    """Uploaded file failed validation."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"File validation failed: {reason}", "FILE_VALIDATION_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AuthError)
    async def auth_error_handler(_req: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_req: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(_req: Request, exc: RateLimitError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(exc.retry_after)},
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(InsufficientCreditsError)
    async def credits_handler(_req: Request, exc: InsufficientCreditsError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(FileValidationError)
    async def file_error_handler(_req: Request, exc: FileValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(PixelMindError)
    async def generic_error_handler(_req: Request, exc: PixelMindError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": exc.code, "message": exc.message},
        )
