import logging
from contextlib import asynccontextmanager
from pathlib import Path
import importlib

from fastapi import FastAPI

logger = logging.getLogger(__name__)

from src.bootstrap.container import get_container
from src.api.routes.auth_routes import auth_router, set_controller
from src.api.routes.password_routes import password_router, verify_router, set_password_controller, set_verify_controller


def _register_legacy_routers(app: FastAPI):
    """注册遗留路由 (app/api/v1/) with /api/v1 prefix"""
    app_dir = Path(__file__).parent.parent.parent / "app"
    api_v1_dir = app_dir / "api" / "v1"
    
    if not api_v1_dir.exists():
        logger.warning(f"Legacy API dir not found: {api_v1_dir}")
        return
    
    migrated_modules = {"password", "verify"}
    
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
                logger.info(f"Registered legacy router: {mod_name} at /api/v1 (tag: {tag})")
        except Exception as e:
            logger.error(f"Failed to register {mod_name}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = get_container()
    set_controller(container.auth_controller)
    set_password_controller(container.password_controller)
    set_verify_controller(container.verify_controller)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Enterprise", lifespan=lifespan)
    
    API_V1_PREFIX = "/api/v1"
    
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(password_router, prefix=API_V1_PREFIX)
    app.include_router(verify_router, prefix=API_V1_PREFIX)
    
    _register_legacy_routers(app)
    
    return app