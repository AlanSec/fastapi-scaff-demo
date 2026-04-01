from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """注册请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码长度至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class RegisterResponse(BaseModel):
    """注册响应模型"""
    id: UUID
    email: str
    username: str
    message: str = "注册成功，请检查邮箱完成验证"


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码长度至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class VerifyEmailRequest(BaseModel):
    """验证邮箱请求模型"""
    token: str = Field(..., description="验证令牌")


class VerifyEmailResponse(BaseModel):
    """验证邮箱响应模型"""
    message: str = "邮箱验证成功"


class ResendVerificationRequest(BaseModel):
    """重新发送验证邮件请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")


class ResendVerificationResponse(BaseModel):
    """重新发送验证邮件响应模型"""
    message: str = "验证邮件已重新发送"


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码长度至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v