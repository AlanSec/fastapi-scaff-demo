from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.application.dto.password_dto import (
    ForgotPasswordInputDTO,
    ForgotPasswordOutputDTO,
    ResetPasswordInputDTO,
    ResetPasswordOutputDTO,
    ChangePasswordInputDTO,
    ChangePasswordOutputDTO,
)
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.password import Password, HashedPassword


@dataclass
class ForgotPasswordUseCase:
    user_repository: UserRepository
    
    async def execute(self, dto: ForgotPasswordInputDTO) -> ForgotPasswordOutputDTO:
        user = await self.user_repository.find_by_email(dto.email, None)
        
        if user is None:
            return ForgotPasswordOutputDTO(
                message="If the email exists, a reset link will be sent"
            )
        
        reset_token = self._generate_reset_token(user)
        
        return ForgotPasswordOutputDTO(
            message=f"Reset token: {reset_token}"
        )
    
    def _generate_reset_token(self, user: User) -> str:
        import secrets
        return f"reset_{secrets.token_urlsafe(32)}"


@dataclass
class ResetPasswordUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher
    
    async def execute(self, dto: ResetPasswordInputDTO) -> ResetPasswordOutputDTO:
        user = await self.user_repository.find_by_reset_token(dto.token)

        if user is None:
            raise ValueError("Invalid or expired reset token")

        new_password = Password(dto.new_password)
        hashed = self.password_hasher.hash(new_password)
        updated_user = replace(
            user,
            hashed_password=hashed,
            reset_token=None,
            reset_token_expires_at=None,
            updated_at=datetime.now()
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
        user_id: UUID
    ) -> ChangePasswordOutputDTO:
        user = await self.user_repository.find_by_id(user_id)
        
        if user is None:
            raise ValueError("User not found")
        
        if not self.password_hasher.verify(Password(dto.current_password), user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        new_password = Password(dto.new_password)
        hashed = self.password_hasher.hash(new_password)
        updated_user = replace(
            user,
            hashed_password=hashed,
            updated_at=datetime.now()
        )

        await self.user_repository.save(updated_user)

        return ChangePasswordOutputDTO(message="Password changed successfully")
