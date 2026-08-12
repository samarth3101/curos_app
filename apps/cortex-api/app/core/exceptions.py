"""Global exception handlers for the FastAPI application.

Registers structured error responses for common exception types.
All errors return a consistent JSON envelope:
    {"error": {"code": "...", "message": "...", "details": [...]}}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)


class CortexError(Exception):
    """Base exception for all Curos domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class NotFoundError(CortexError):
    def __init__(self, resource: str, identifier: str | None = None) -> None:
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(message, code="NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(CortexError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, code="UNAUTHORIZED", status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(CortexError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, code="FORBIDDEN", status_code=status.HTTP_403_FORBIDDEN)


class ConflictError(CortexError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFLICT", status_code=status.HTTP_409_CONFLICT)


class ValidationDomainError(CortexError):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


def _error_response(
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or []}}


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(CortexError)
    async def cortex_error_handler(request: Request, exc: CortexError) -> JSONResponse:
        logger.warning(
            "domain_error",
            code=exc.code,
            message=exc.message,
            path=str(request.url),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        logger.info("validation_error", path=str(request.url), errors=details)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_response("VALIDATION_ERROR", "Request validation failed", details),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_response("VALIDATION_ERROR", "Data validation failed", exc.errors()),  # type: ignore[arg-type]
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_error",
            path=str(request.url),
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_response("INTERNAL_ERROR", "An unexpected error occurred"),
        )
