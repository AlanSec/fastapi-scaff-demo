import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.api.controllers.auth_controller import AuthController
from src.api.schemas.auth_schema import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenResponse,
)
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.dto.auth_dto import RegisterUserOutputDTO, LoginUserOutputDTO


class TestAuthController:
    @pytest.fixture
    def mock_register_use_case(self):
        return AsyncMock(spec=RegisterUserUseCase)

    @pytest.fixture
    def mock_login_use_case(self):
        return AsyncMock(spec=LoginUserUseCase)

    @pytest.fixture
    def controller(self, mock_register_use_case, mock_login_use_case):
        return AuthController(
            register_use_case=mock_register_use_case,
            login_use_case=mock_login_use_case,
        )

    @pytest.mark.asyncio
    async def test_register_creates_user(self, controller, mock_register_use_case):
        tenant_id = uuid4()
        request = RegisterRequest(
            email="test@example.com",
            password="Password123",
            tenant_id=str(tenant_id),
        )

        mock_register_use_case.execute.return_value = RegisterUserOutputDTO(
            user_id=uuid4(),
            email="test@example.com",
            tenant_id=tenant_id,
            is_verified=False,
        )

        result = await controller.register(request)

        assert isinstance(result, RegisterResponse)
        assert result.email == "test@example.com"
        mock_register_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_returns_tokens(self, controller, mock_login_use_case):
        tenant_id = uuid4()
        user_id = uuid4()
        request = LoginRequest(
            email="test@example.com",
            password="Password123",
            tenant_id=str(tenant_id),
        )

        mock_login_use_case.execute.return_value = LoginUserOutputDTO(
            user_id=user_id,
            email="test@example.com",
            tenant_id=tenant_id,
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=1800,
        )

        result = await controller.login(request)

        assert isinstance(result, LoginResponse)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"

    @pytest.mark.asyncio
    async def test_to_token_response(self, controller):
        tenant_id = uuid4()
        login_result = LoginUserOutputDTO(
            user_id=uuid4(),
            email="test@example.com",
            tenant_id=tenant_id,
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=1800,
        )

        result = controller.to_token_response(login_result)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        assert result.token_type == "bearer"