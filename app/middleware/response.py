import json

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from toollib.utils import now2timestamp


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """响应包装中间件 - 为所有成功响应添加统一格式"""

    EXCLUDED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/media",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        response = await call_next(request)

        if response.status_code >= 400:
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body += chunk.encode("utf-8")
            else:
                body += chunk

        try:
            content = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        if isinstance(content, dict) and "code" in content and "time" in content and "msg" in content:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        wrapped_content = {
            "time": now2timestamp(),
            "msg": "操作成功",
            "code": 0,
            "data": content,
        }

        return JSONResponse(
            content=wrapped_content,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
        )
