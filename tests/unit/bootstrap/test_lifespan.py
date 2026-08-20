import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.bootstrap.config import Settings
from src.bootstrap.container import get_container
from src.bootstrap.lifespan import create_app, lifespan


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_is_context_manager(self):
        app = FastAPI()

        manager = lifespan(app)
        assert hasattr(manager, "__aenter__")
        assert hasattr(manager, "__aexit__")


class TestCreateApp:
    def test_create_app_returns_fastapi_instance(self):
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_create_app_has_correct_title(self):
        app = create_app()
        assert app.title == "FastAPI Enterprise"

    def test_create_app_includes_auth_router(self):
        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/api/v1/auth/register" in routes
        assert "/api/v1/auth/login" in routes

    def test_create_app_has_lifespan_context_manager(self):
        app = create_app()
        assert hasattr(app, "router")
        assert hasattr(app.router, "lifespan_context")

    def test_create_app_routes_have_correct_methods(self):
        app = create_app()
        route_methods = {}
        for route in app.routes:
            if hasattr(route, "methods"):
                for method in route.methods:
                    route_methods[route.path] = method

        assert "POST" in route_methods.get("/api/v1/auth/register", set())
        assert "POST" in route_methods.get("/api/v1/auth/login", set())

    def test_create_app_registers_cors_middleware_with_default_origins(self):
        app = create_app()
        cors = [m for m in app.user_middleware if m.cls is CORSMiddleware]
        assert cors
        assert "http://localhost:5173" in cors[0].kwargs["allow_origins"]

    def test_create_app_reads_cors_origins_from_config(self, monkeypatch):
        container = get_container()
        monkeypatch.setattr(container, "_config", Settings(cors_origins="https://frontend.example.com"))

        app = create_app()
        cors = [m for m in app.user_middleware if m.cls is CORSMiddleware]
        assert cors
        assert cors[0].kwargs["allow_origins"] == ["https://frontend.example.com"]
