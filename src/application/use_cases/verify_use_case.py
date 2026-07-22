from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime
from typing import Optional

from src.application.dto.password_dto import (
    VerifyEmailInputDTO,
    VerifyEmailOutputDTO,
    ResendVerificationInputDTO,
    ResendVerificationOutputDTO,
)
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


@dataclass
class VerifyEmailUseCase:
    user_repository: UserRepository
    
    async def execute(self, dto: VerifyEmailInputDTO) -> VerifyEmailOutputDTO:
        user = await self.user_repository.find_by_verification_token(dto.token)
        
        if user is None:
            raise ValueError("Invalid verification token")

        updated_user = replace(
            user,
            is_verified=True,
            verification_token=None,
            updated_at=datetime.now()
        )

        await self.user_repository.save(updated_user)

        return VerifyEmailOutputDTO(
            message="Email verified successfully",
            is_verified=True
        )


@dataclass
class ResendVerificationUseCase:
    user_repository: UserRepository
    
    async def execute(self, dto: ResendVerificationInputDTO) -> ResendVerificationOutputDTO:
        user = await self.user_repository.find_by_email(dto.email, None)
        
        if user is None:
            return ResendVerificationOutputDTO(
                message="If the email exists, a verification link will be sent"
            )
        
        if user.is_verified:
            return ResendVerificationOutputDTO(
                message="Email is already verified"
            )
        
        verification_token = self._generate_verification_token()
        
        return ResendVerificationOutputDTO(
            message=f"Verification token: {verification_token}"
        )
    
    def _generate_verification_token(self) -> str:
        import secrets
        return f"verify_{secrets.token_urlsafe(32)}"
