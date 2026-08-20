import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from src.api.middleware.exception_handlers import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.api.routes.auth_routes import auth_router
from src.api.routes.password_routes import password_router, verify_router
from src.api.routes.permission_routes import permission_router
from src.api.routes.role_routes import role_router
from src.api.routes.tenant_routes import tenant_router
from src.api.routes.user_admin_routes import user_admin_router
from src.bootstrap.container import get_container
from src.bootstrap.ensure_admin import ensure_admin_user
from src.infrastructure.persistence.database import init_db
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表失败应直接暴露（数据库不可用时应用不应带病启动）
    await init_db()

    try:
        await ensure_admin_user()
    except Exception as e:
        logger.error("Failed to create admin user: %s", e)

    yield


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
    # 统一错误响应格式（HTTPException / 校验错误 / 未处理异常均带 code 字段）
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """健康检查（部署探活用，不鉴权）"""
        return {"status": "ok"}

    API_V1_PREFIX = "/api/v1"

    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(password_router, prefix=API_V1_PREFIX)
    app.include_router(verify_router, prefix=API_V1_PREFIX)
    app.include_router(tenant_router, prefix=API_V1_PREFIX)
    app.include_router(role_router, prefix=API_V1_PREFIX)
    app.include_router(permission_router, prefix=API_V1_PREFIX)
    app.include_router(user_admin_router, prefix=API_V1_PREFIX)

    return app
