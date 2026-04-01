from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterUserInputDTO:
    """用户注册输入 DTO"""
    email: str
    password: str
    tenant_id: UUID


@dataclass(frozen=True)
class RegisterUserOutputDTO:
    """用户注册输出 DTO"""
    user_id: UUID
    email: str
    tenant_id: UUID
    is_verified: bool


@dataclass(frozen=True)
class LoginUserInputDTO:
    """用户登录输入 DTO"""
    email: str
    password: str
    tenant_id: UUID


@dataclass(frozen=True)
class LoginUserOutputDTO:
    """用户登录输出 DTO"""
    user_id: UUID
    email: str
    tenant_id: UUID
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True)
class ForgotPasswordInputDTO:
    """忘记密码输入 DTO"""
    email: str


@dataclass(frozen=True)
class ForgotPasswordOutputDTO:
    """忘记密码输出 DTO"""
    message: str


@dataclass(frozen=True)
class ResetPasswordInputDTO:
    """重置密码输入 DTO"""
    token: str
    new_password: str


@dataclass(frozen=True)
class ResetPasswordOutputDTO:
    """重置密码输出 DTO"""
    message: str


@dataclass(frozen=True)
class ChangePasswordInputDTO:
    """修改密码输入 DTO"""
    current_password: str
    new_password: str


@dataclass(frozen=True)
class ChangePasswordOutputDTO:
    """修改密码输出 DTO"""
    message: str