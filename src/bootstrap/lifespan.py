import logging
from contextlib import asynccontextmanager
from pathlib import Path
import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.api.middleware.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

logger = logging.getLogger(__name__)

from src.bootstrap.container import get_container
from src.bootstrap.ensure_admin import ensure_admin_user
from src.api.routes.auth_routes import auth_router, set_controller
from src.api.routes.tenant_routes import tenant_router, set_tenant_controller
from src.api.routes.role_routes import role_router, set_role_controller
from src.api.routes.permission_routes import permission_router, set_permission_controller
from src.api.routes.user_admin_routes import user_admin_router, set_user_admin_controller
from src.api.routes.password_routes import password_router, verify_router, set_password_controller, set_verify_controller
from app.db.session import init_db


def _register_legacy_routers(app: FastAPI):
    """Register legacy routers from app/api/v1/ with /api/v1 prefix"""
    app_dir = Path(__file__).parent.parent.parent / "app"
    api_v1_dir = app_dir / "api" / "v1"

    if not api_v1_dir.exists():
        logger.warning("Legacy API dir not found: %s", api_v1_dir)
        return

    for item in api_v1_dir.iterdir():
        if item.name.startswith("__") or not item.name.endswith(".py"):
            continue

        mod_name = item.stem
        if mod_name in migrated_modules:
            continue

        try:
            mod = importlib.import_module(f"app.api.v1.{mod_name}")
            router_name = f"{mod_name}_router"
            if hasattr(mod, router_name):
                router = getattr(mod, router_name)
                tag = getattr(mod, "_tag", mod_name)
                app.include_router(router, prefix="/api/v1", tags=[tag])
                logger.info("Registered legacy router: %s at /api/v1 (tag: %s)", mod_name, tag)
        except Exception as e:
            logger.error("Failed to register %s: %s", mod_name, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    try:
        await init_db()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning("Database init skipped (tables may already exist): %s", e)

    container = get_container()
    set_controller(container.auth_controller)
    set_password_controller(container.password_controller)
    set_verify_controller(container.verify_controller)
    set_tenant_controller(container.tenant_controller)
    set_role_controller(container.role_controller)
    set_permission_controller(container.permission_controller)
    set_user_admin_controller(container.user_admin_controller)

    # Ensure default admin user exists
    try:
        await ensure_admin_user()
    except Exception as e:
        logger.error("Failed to create admin user: %s", e)

    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Enterprise", lifespan=lifespan)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    class RequestLogMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            logger.info("%s %s", request.method, request.url.path)
            return await call_next(request)

    app.add_middleware(RequestLogMiddleware)

    # Exception handlers
    app.add_exception_handler(Exception, general_exception_handler)

    API_V1_PREFIX = "/api/v1"
    API_V1_PREFIX = "/api/v1"

    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(password_router, prefix=API_V1_PREFIX)
    app.include_router(verify_router, prefix=API_V1_PREFIX)
    app.include_router(tenant_router, prefix=API_V1_PREFIX)
    app.include_router(role_router, prefix=API_V1_PREFIX)
    app.include_router(permission_router, prefix=API_V1_PREFIX)
    app.include_router(user_admin_router, prefix=API_V1_PREFIX)

    _register_legacy_routers(app)

    return app
