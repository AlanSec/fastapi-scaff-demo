from unittest.mock import AsyncMock

import pytest
from src.api.controllers.auth_controller import AuthController
from src.api.routes.auth_routes import auth_router
from src.api.schemas.auth_schema import LoginResponse, RegisterResponse


class TestAuthRoutes:
    @pytest.fixture
    def mock_controller(self):
        controller = AsyncMock(spec=AuthController)
        controller.register.return_value = RegisterResponse(
            user_id="test-id",
            email="test@example.com",
            tenant_id="tenant-id",
            is_verified=False,
        )
        controller.login.return_value = LoginResponse(
            user_id="test-id",
            email="test@example.com",
            tenant_id="tenant-id",
            access_token="access",
            refresh_token="refresh",
            expires_in=1800,
        )
        return controller

    def test_router_has_correct_prefix(self):
        assert auth_router.prefix == "/auth"

    def test_router_has_correct_tags(self):
        assert auth_router.tags == ["auth"]

    def test_router_has_register_endpoint(self):
        routes = [route.path for route in auth_router.routes]
        assert "/auth/register" in routes

    def test_router_has_login_endpoint(self):
        routes = [route.path for route in auth_router.routes]
        assert "/auth/login" in routes

    def test_router_has_login_json_endpoint(self):
        routes = [route.path for route in auth_router.routes]
        assert "/auth/login/json" in routes

    def test_router_has_refresh_endpoint(self):
        routes = [route.path for route in auth_router.routes]
        assert "/auth/refresh" in routes
