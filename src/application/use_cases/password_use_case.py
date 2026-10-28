from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.application.dto.password_dto import (
    ChangePasswordInputDTO,
    ChangePasswordOutputDTO,
    ForgotPasswordInputDTO,
    ForgotPasswordOutputDTO,
    ResetPasswordInputDTO,
    ResetPasswordOutputDTO,
)
from src.domain.entities.user import User
from src.domain.exceptions import InvalidCredentialsError
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.email_interfaces import EmailSender
from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.password import Password

RESET_TOKEN_EXPIRE_MINUTES = 30
GENERIC_FORGOT_MESSAGE = "If the email exists, a reset link will be sent"


@dataclass
class ForgotPasswordUseCase:
    user_repository: UserRepository
    email_sender: EmailSender

    async def execute(self, dto: ForgotPasswordInputDTO) -> ForgotPasswordOutputDTO:
        user = await self.user_repository.find_by_email(dto.email, None)

        if user is None:
            return ForgotPasswordOutputDTO(message=GENERIC_FORGOT_MESSAGE)

        reset_token = self._generate_reset_token(user)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        updated_user = user.with_reset_token(reset_token, expires_at)
        await self.user_repository.save(updated_user)

        await self.email_sender.send(
            to=str(user.email),
            subject="Password Reset",
            body=f"Your password reset token is: {reset_token}\n"
                 f"It expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.",
        )

        return ForgotPasswordOutputDTO(message=GENERIC_FORGOT_MESSAGE)

    def _generate_reset_token(self, user: User) -> str:
        import secrets
        return f"reset_{secrets.token_urlsafe(32)}"


@dataclass
class ResetPasswordUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, dto: ResetPasswordInputDTO) -> ResetPasswordOutputDTO:
        user = await self.user_repository.find_by_reset_token(dto.token)

        if user is None or user.reset_token_expires_at is None:
            raise InvalidCredentialsError("Invalid or expired reset token")

        expires_at = user.reset_token_expires_at
        if expires_at.tzinfo is None:
            # SQLite 旧数据可能为 naive datetime，统一按 UTC 处理
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            raise InvalidCredentialsError("Invalid or expired reset token")

        new_password = Password(dto.new_password)
        hashed = self.password_hasher.hash(new_password)
        updated_user = replace(
            user.clear_reset_token(),
            password=hashed,
            updated_at=datetime.now(timezone.utc)
        )

        await self.user_repository.save(updated_user)

        return ResetPasswordOutputDTO(message="Password reset successful")


@dataclass
class ChangePasswordUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(
        self,
        dto: ChangePasswordInputDTO,
        user_id: UUID,
        tenant_id: UUID,
    ) -> ChangePasswordOutputDTO:
        user = await self.user_repository.find_by_id(user_id, tenant_id)

        if user is None:
            raise InvalidCredentialsError("User not found")

        if not self.password_hasher.verify(Password(dto.current_password), user.password):
            raise InvalidCredentialsError("Current password is incorrect")

        new_password = Password(dto.new_password)
        hashed = self.password_hasher.hash(new_password)
        updated_user = replace(
            user,
            password=hashed,
            updated_at=datetime.now(timezone.utc)
        )

        await self.user_repository.save(updated_user)

        return ChangePasswordOutputDTO(message="Password changed successfully")
