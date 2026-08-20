"""Auth Controller - Handles HTTP request/response mapping"""
from uuid import UUID

from src.api.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from src.application.dto.auth_dto import (
    LoginUserInputDTO,
    LoginUserOutputDTO,
    RefreshTokenInputDTO,
    RegisterUserInputDTO,
)
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase


class AuthController:
    def __init__(
        self,
        register_use_case: RegisterUserUseCase,
        login_use_case: LoginUserUseCase,
        refresh_use_case: RefreshTokenUseCase,
    ):
        self._register_use_case = register_use_case
        self._login_use_case = login_use_case
        self._refresh_use_case = refresh_use_case

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        dto = RegisterUserInputDTO(
            email=request.email,
            password=request.password,
            tenant_id=UUID(request.tenant_id) if request.tenant_id else None,
        )
        result = await self._register_use_case.execute(dto)

        return RegisterResponse(
            user_id=str(result.user_id),
            email=result.email,
            tenant_id=str(result.tenant_id),
            is_verified=result.is_verified,
        )

    async def login(self, request: LoginRequest) -> LoginResponse:
        dto = LoginUserInputDTO(
            email=request.email,
            password=request.password,
            tenant_id=UUID(request.tenant_id),
        )
        result = await self._login_use_case.execute(dto)

        return LoginResponse(
            user_id=str(result.user_id),
            email=result.email,
            tenant_id=str(result.tenant_id),
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            expires_in=result.expires_in,
        )

    def to_token_response(self, login_result: LoginUserOutputDTO) -> TokenResponse:
        return TokenResponse(
            access_token=login_result.access_token,
            refresh_token=login_result.refresh_token,
        )

    async def refresh(self, request: RefreshTokenRequest) -> TokenResponse:
        dto = RefreshTokenInputDTO(refresh_token=request.refresh_token)
        result = await self._refresh_use_case.execute(dto)
        return TokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
        )
