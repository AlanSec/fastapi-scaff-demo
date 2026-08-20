from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from src.api.controllers.auth_controller import AuthController
from src.api.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from src.application.dto.auth_dto import LoginUserOutputDTO, RegisterUserOutputDTO
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase


class TestAuthController:
    @pytest.fixture
    def mock_register_use_case(self):
        return AsyncMock(spec=RegisterUserUseCase)

    @pytest.fixture
    def mock_login_use_case(self):
        return AsyncMock(spec=LoginUserUseCase)

    @pytest.fixture
    def mock_refresh_use_case(self):
        return AsyncMock(spec=RefreshTokenUseCase)

    @pytest.fixture
    def controller(self, mock_register_use_case, mock_login_use_case, mock_refresh_use_case):
        return AuthController(
            register_use_case=mock_register_use_case,
            login_use_case=mock_login_use_case,
            refresh_use_case=mock_refresh_use_case,
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

    @pytest.mark.asyncio
    async def test_refresh_returns_new_tokens(self, controller, mock_refresh_use_case):
        mock_refresh_use_case.execute.return_value = LoginUserOutputDTO(
            user_id=uuid4(),
            email="test@example.com",
            tenant_id=uuid4(),
            access_token="new_access",
            refresh_token="new_refresh",
            expires_in=1800,
        )

        result = await controller.refresh(RefreshTokenRequest(refresh_token="old_refresh"))

        assert isinstance(result, TokenResponse)
        assert result.access_token == "new_access"
        assert result.refresh_token == "new_refresh"
        mock_refresh_use_case.execute.assert_called_once()
