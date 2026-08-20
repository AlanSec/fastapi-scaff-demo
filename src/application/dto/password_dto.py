from dataclasses import dataclass


@dataclass(frozen=True)
class ForgotPasswordInputDTO:
    email: str


@dataclass(frozen=True)
class ForgotPasswordOutputDTO:
    message: str


@dataclass(frozen=True)
class ResetPasswordInputDTO:
    token: str
    new_password: str


@dataclass(frozen=True)
class ResetPasswordOutputDTO:
    message: str


@dataclass(frozen=True)
class ChangePasswordInputDTO:
    current_password: str
    new_password: str


@dataclass(frozen=True)
class ChangePasswordOutputDTO:
    message: str


@dataclass(frozen=True)
class VerifyEmailInputDTO:
    token: str


@dataclass(frozen=True)
class VerifyEmailOutputDTO:
    message: str
    is_verified: bool


@dataclass(frozen=True)
class ResendVerificationInputDTO:
    email: str


@dataclass(frozen=True)
class ResendVerificationOutputDTO:
    message: str
