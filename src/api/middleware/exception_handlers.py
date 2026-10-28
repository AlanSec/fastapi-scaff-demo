"""FastAPI exception handlers — standardized JSON error responses."""
import logging
import traceback

from fastapi.exceptions import RequestValidationError
from src.domain.exceptions import (
    ConflictError,
    DomainError,
    EntityNotFoundError,
    InvalidCredentialsError,
)
from src.domain.services.security_interfaces import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def _domain_status(exc: DomainError) -> int:
    """领域异常 → HTTP 状态码"""
    if isinstance(exc, EntityNotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, InvalidCredentialsError):
        return 401
    return 400


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """领域异常统一映射：NotFound→404 / Conflict→409 / InvalidCredentials→401 / 其他→400"""
    status_code = _domain_status(exc)
    logger.warning(
        "Domain error %s (%s): %s %s",
        status_code,
        type(exc).__name__,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc), "code": status_code},
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """裸 ValueError 兜底（如值对象校验失败）→ 400"""
    logger.warning("Value error: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "code": 400},
    )


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning("Rate limited: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc), "code": 429},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning("HTTP %s: %s %s", exc.status_code, request.method, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.status_code},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    msg = ", ".join(f"'{e['loc'][-1]}' {e['msg']}" for e in errors)
    logger.warning("Validation error: %s %s — %s", request.method, request.url.path, msg)
    return JSONResponse(
        status_code=422,
        content={"detail": msg, "code": 422},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error: %s %s\n%s", request.method, request.url.path, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": 500},
    )
