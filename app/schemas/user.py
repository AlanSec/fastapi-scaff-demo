from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserBase(BaseModel):
    """用户基础模式"""

    email: str
    username: str
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """创建用户的请求模式"""
    password: str
    tenant_id: UUID


class UserUpdate(BaseModel):
    """更新用户的请求模式"""

    email: str | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    tenant_id: UUID | None = None


class UserRead(UserBase):
    """用户响应模式"""

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """配置类"""

        from_attributes = True
