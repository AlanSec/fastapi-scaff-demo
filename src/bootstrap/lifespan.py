import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from src.api.middleware.exception_handlers import (
    domain_exception_handler,
    general_exception_handler,
    http_exception_handler,
    rate_limit_handler,
    validation_exception_handler,
    value_error_handler,
)
from src.api.routes import API_VERSIONS
from src.bootstrap.container import get_container
from src.bootstrap.ensure_admin import ensure_admin_user
from src.domain.exceptions import DomainError
from src.domain.services.security_interfaces import RateLimitExceeded
from src.infrastructure.persistence.database import init_db
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

_REFRESH_TOKEN_CLEANUP_INTERVAL_SECONDS = 3600


async def _refresh_token_cleanup_loop() -> None:
    """周期清理过期 refresh token（每小时），避免表无限增长。

    清理从热路径（每次登录/轮换的写操作）移到这里，避免写放大。
    """
    while True:
        await asyncio.sleep(_REFRESH_TOKEN_CLEANUP_INTERVAL_SECONDS)
        try:
            deleted = await get_container().refresh_token_repository.delete_expired(
                datetime.now(timezone.utc)
            )
            if deleted:
                logger.info("Cleaned up %d expired refresh tokens", deleted)
        except Exception:  # noqa: BLE001 - 后台任务不允许崩溃
            logger.exception("Refresh token cleanup failed (will retry next cycle)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表失败应直接暴露（数据库不可用时应用不应带病启动）
    await init_db()

    # admin 初始化失败同样不允许带病启动（与 init_db 策略一致）：
    # admin 缺失时登录/管理链路不可用，且难以事后察觉
    await ensure_admin_user()

    cleanup_task = asyncio.create_task(_refresh_token_cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Enterprise", lifespan=lifespan)

    # CORS 白名单来自配置（CORS_ORIGINS，逗号分隔），避免改代码
    cors_origins = [
        o.strip()
        for o in get_container().config.cors_origins.split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class RequestLogMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            logger.info("%s %s", request.method, request.url.path)
            return await call_next(request)

    app.add_middleware(RequestLogMiddleware)
    # 统一错误响应格式（HTTPException / 校验错误 / 领域异常 / 未处理异常均带 code 字段）
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # 领域异常（DomainError 继承 ValueError，按 MRO 优先命中精确 handler）
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """健康检查（部署探活用，不鉴权）"""
        return {"status": "ok"}

    # 按版本注册路由（API_VERSIONS 注册表：见 src/api/routes/__init__.py）
    for version, routers in API_VERSIONS.items():
        for router in routers:
            app.include_router(router, prefix=f"/api/{version}")

    return app
