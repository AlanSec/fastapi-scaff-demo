from dataclasses import dataclass

from src.application.dto.password_dto import (
    ResendVerificationInputDTO,
    ResendVerificationOutputDTO,
    VerifyEmailInputDTO,
    VerifyEmailOutputDTO,
)
from src.domain.exceptions import InvalidCredentialsError
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.email_interfaces import EmailSender

GENERIC_VERIFY_MESSAGE = "If the email exists, a verification link will be sent"


@dataclass
class VerifyEmailUseCase:
    user_repository: UserRepository

    async def execute(self, dto: VerifyEmailInputDTO) -> VerifyEmailOutputDTO:
        user = await self.user_repository.find_by_verification_token(dto.token)

        if user is None:
            raise InvalidCredentialsError("Invalid verification token")

        updated_user = user.verify().clear_verification_token()

        await self.user_repository.save(updated_user)

        return VerifyEmailOutputDTO(
            message="Email verified successfully",
            is_verified=True
        )


@dataclass
class ResendVerificationUseCase:
    user_repository: UserRepository
    email_sender: EmailSender

    async def execute(self, dto: ResendVerificationInputDTO) -> ResendVerificationOutputDTO:
        user = await self.user_repository.find_by_email(dto.email, None)

        if user is None:
            return ResendVerificationOutputDTO(message=GENERIC_VERIFY_MESSAGE)

        if user.is_verified:
            return ResendVerificationOutputDTO(
                message="Email is already verified"
            )

        verification_token = self._generate_verification_token()
        updated_user = user.with_verification_token(verification_token)
        await self.user_repository.save(updated_user)

        await self.email_sender.send(
            to=str(user.email),
            subject="Email Verification",
            body=f"Your email verification token is: {verification_token}",
        )

        return ResendVerificationOutputDTO(message=GENERIC_VERIFY_MESSAGE)

    def _generate_verification_token(self) -> str:
        import secrets
        return f"verify_{secrets.token_urlsafe(32)}"
