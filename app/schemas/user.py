from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """用户基础模式"""

    email: str
    username: str
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """创建用户的请求模式"""
    password: str = Field(..., min_length=8, max_length=100)
    tenant_id: UUID

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


class UserUpdateMe(BaseModel):
    """普通用户更新自己的信息（不含敏感字段）"""

    email: str | None = None
    username: str | None = None
    password: str | None = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('密码长度至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserUpdate(BaseModel):
    """管理员更新用户的请求模式（包含敏感字段）"""

    email: str | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    tenant_id: UUID | None = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('密码长度至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserRead(UserBase):
    """用户响应模式"""

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """配置类"""

        from_attributes = True
