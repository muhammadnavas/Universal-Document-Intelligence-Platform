"""
Custom Exceptions and Exception Handlers
========================================
Provides a structured error response hierarchy and FastAPI exception handlers.

All errors return a consistent JSON envelope:
{
    "error": "ErrorClassName",
    "message": "Human-readable message",
    "status_code": 422
}
"""
import logging
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Custom Exception Hierarchy ────────────────────────────────────────────────

class UDIPException(Exception):
    """Base exception for all UDIP errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Any = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class FileSizeTooLargeError(UDIPException):
    status_code = 413
    error_code = "FILE_TOO_LARGE"


class UnsupportedFileTypeError(UDIPException):
    status_code = 415
    error_code = "UNSUPPORTED_FILE_TYPE"


class FileNotFoundError(UDIPException):  # noqa: A001 (shadows built-in intentionally in UDIP namespace)
    status_code = 404
    error_code = "FILE_NOT_FOUND"


class ExtractionError(UDIPException):
    status_code = 422
    error_code = "EXTRACTION_FAILED"


class ExportError(UDIPException):
    status_code = 500
    error_code = "EXPORT_FAILED"


# ── Exception Handlers ────────────────────────────────────────────────────────

async def udip_exception_handler(request: Request, exc: UDIPException) -> JSONResponse:
    """Handle all UDIP domain exceptions."""
    logger.warning(
        "UDIP error [%s] on %s %s: %s",
        exc.error_code, request.method, request.url.path, exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


async def validation_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle generic ValueError as a 422 validation error."""
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": str(exc),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors — prevents stack traces leaking to clients."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please check server logs.",
        },
    )
