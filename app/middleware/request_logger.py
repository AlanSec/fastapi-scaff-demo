import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 记录请求头信息用于调试"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_header = request.headers.get("authorization", "")
        if auth_header:
            logger.info(f"请求 {request.method} {request.url.path}")
            logger.info(f"Authorization: {auth_header[:50]}..." if len(auth_header) > 50 else f"Authorization: {auth_header}")

        response = await call_next(request)
        return response
