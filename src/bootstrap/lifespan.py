from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.bootstrap.container import get_container
from src.api.routes.auth_routes import auth_router, set_controller
from src.api.routes.password_routes import password_router, verify_router, set_password_controller, set_verify_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = get_container()
    set_controller(container.auth_controller)
    set_password_controller(container.password_controller)
    set_verify_controller(container.verify_controller)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Enterprise", lifespan=lifespan)
    app.include_router(auth_router)
    app.include_router(password_router)
    app.include_router(verify_router)
    return app