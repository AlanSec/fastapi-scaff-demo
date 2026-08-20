"""API Schemas for Auth endpoints"""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")
    tenant_id: str | None = Field(None, description="租户ID（为空时自动创建独立租户）")


class RegisterResponse(BaseModel):
    """用户注册响应"""
    user_id: str
    email: str
    tenant_id: str
    is_verified: bool


class LoginRequest(BaseModel):
    """用户登录请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")
    tenant_id: str = Field(..., description="租户ID")


class LoginResponse(BaseModel):
    """用户登录响应"""
    user_id: str
    email: str
    tenant_id: str
    access_token: str
    refresh_token: str
    expires_in: int


class TokenResponse(BaseModel):
    """Token 响应 (兼容旧 API)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class OAuth2TokenResponse(BaseModel):
    """OAuth2 令牌响应（RFC 6749）"""
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr = Field(..., description="用户邮箱")


class ForgotPasswordResponse(BaseModel):
    """忘记密码响应"""
    message: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., description="新密码")


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    message: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., description="新密码")


class ChangePasswordResponse(BaseModel):
    """修改密码响应"""
    message: str


class VerifyEmailRequest(BaseModel):
    """邮箱验证请求"""
    token: str = Field(..., description="验证令牌")


class VerifyEmailResponse(BaseModel):
    """邮箱验证响应"""
    message: str
    is_verified: bool


class ResendVerificationRequest(BaseModel):
    """重新发送验证邮件请求"""
    email: EmailStr = Field(..., description="用户邮箱")


class ResendVerificationResponse(BaseModel):
    """重新发送验证邮件响应"""
    message: str
