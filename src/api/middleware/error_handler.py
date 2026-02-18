from typing import Any

from connexion import problem
from connexion.exceptions import ProblemException
from pydantic import ValidationError
from starlette.requests import Request

from logger import logger
from models.dtos import ErrorResponse
from shared.exceptions import AppError, NotFoundException


async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning(
        "Validation error", extra={"path": request.url.path, "errors": exc.errors()}
    )
    payload = ErrorResponse(
        error="bad_request",
        message="Validation failed",
        details={"errors": exc.errors()},
    )
    return problem(
        status=400,
        title="Bad Request",
        detail="Validation failed",
        ext=payload.model_dump(mode="json"),
    )


async def http_exception_handler(request: Request, exc: ProblemException):
    logger.warning(
        "HTTP exception",
        extra={"path": request.url.path, "status": exc.status, "detail": exc.detail},
    )
    payload = ErrorResponse(
        error=exc.title or "error",
        message=exc.detail or "An error occurred",
        details=exc.ext or {},
    )
    return problem(
        status=exc.status,
        title=exc.title or "error",
        detail=exc.detail or "An error occurred",
        ext=payload.model_dump(mode="json"),
    )


async def app_exception_handler(request: Request, exc: AppError):
    """Handle custom application exceptions."""
    status_code = 500
    if isinstance(exc, NotFoundException):
        status_code = 404
    logger.info(
        f"App exception: {exc.__class__.__name__}",
        extra={"path": request.url.path, "message": exc.message},
    )

    payload = ErrorResponse(
        error=exc.__class__.__name__.lower().replace("exception", ""),
        message=exc.message,
        details=exc.details,
    )
    return problem(
        status=status_code,
        title=payload.error,
        detail=payload.message,
        ext=payload.model_dump(mode="json"),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        extra={"path": request.url.path, "error": str(exc)},
        exc_info=True,
    )
    payload = ErrorResponse(
        error="server_error",
        message="Internal server error",
    )
    return problem(
        status=500,
        title="server_error",
        detail="Internal server error",
        ext=payload.model_dump(mode="json"),
    )
