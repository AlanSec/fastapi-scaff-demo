import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.response import Response
from app.api.status import Status


class SimpleRateLimiter:
    def __init__(self):
        self._requests = defaultdict(list)
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        self._requests[key] = [
            ts for ts in self._requests[key]
            if now - ts < window_seconds
        ]
        if len(self._requests[key]) >= max_requests:
            return False
        self._requests[key].append(now)
        return True
    
    def get_client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return f"{ip}:{request.url.path}"


_rate_limiter = SimpleRateLimiter()


def rate_limit(max_requests: int, window_seconds: int = 60):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            key = _rate_limiter.get_client_key(request)
            if not _rate_limiter.is_allowed(key, max_requests, window_seconds):
                return Response.failure(
                    msg="请求过于频繁，请稍后再试",
                    code=Status.RATE_LIMIT_ERROR.code
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    return Response.failure(
        msg="请求过于频繁，请稍后再试",
        code=Status.RATE_LIMIT_ERROR.code
    )


def get_limiter():
    return _rate_limiter
