import pytest
from fastapi import FastAPI

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