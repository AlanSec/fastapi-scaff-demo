"""Password Controller - Handles password management endpoints"""
from uuid import UUID

from src.api.schemas.auth_schema import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from src.application.dto.password_dto import (
    ChangePasswordInputDTO,
    ForgotPasswordInputDTO,
    ResendVerificationInputDTO,
    ResetPasswordInputDTO,
    VerifyEmailInputDTO,
)
from src.application.use_cases.password_use_case import (
    ChangePasswordUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
)
from src.application.use_cases.verify_use_case import ResendVerificationUseCase, VerifyEmailUseCase


class PasswordController:
    def __init__(
        self,
        forgot_password_use_case: ForgotPasswordUseCase,
        reset_password_use_case: ResetPasswordUseCase,
        change_password_use_case: ChangePasswordUseCase,
    ):
        self._forgot_use_case = forgot_password_use_case
        self._reset_use_case = reset_password_use_case
        self._change_use_case = change_password_use_case

    async def forgot_password(self, request: ForgotPasswordRequest) -> ForgotPasswordResponse:
        dto = ForgotPasswordInputDTO(email=request.email)
        result = await self._forgot_use_case.execute(dto)
        return ForgotPasswordResponse(message=result.message)

    async def reset_password(self, request: ResetPasswordRequest) -> ResetPasswordResponse:
        dto = ResetPasswordInputDTO(
            token=request.token,
            new_password=request.new_password
        )
        result = await self._reset_use_case.execute(dto)
        return ResetPasswordResponse(message=result.message)

    async def change_password(
        self,
        request: ChangePasswordRequest,
        user_id: UUID,
        tenant_id: UUID,
    ) -> ChangePasswordResponse:
        dto = ChangePasswordInputDTO(
            current_password=request.current_password,
            new_password=request.new_password
        )
        result = await self._change_use_case.execute(dto, user_id, tenant_id)
        return ChangePasswordResponse(message=result.message)


class VerifyController:
    def __init__(self, verify_use_case: 'VerifyEmailUseCase', resend_use_case: 'ResendVerificationUseCase'):
        self._verify_use_case = verify_use_case
        self._resend_use_case = resend_use_case

    async def verify_email(self, request: VerifyEmailRequest) -> VerifyEmailResponse:
        dto = VerifyEmailInputDTO(token=request.token)
        result = await self._verify_use_case.execute(dto)
        return VerifyEmailResponse(
            message=result.message,
            is_verified=result.is_verified
        )

    async def resend_verification(self, request: ResendVerificationRequest) -> ResendVerificationResponse:
        dto = ResendVerificationInputDTO(email=request.email)
        result = await self._resend_use_case.execute(dto)
        return ResendVerificationResponse(message=result.message)
