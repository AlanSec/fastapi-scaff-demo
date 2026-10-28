"""User admin schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminCreateUserRequest(BaseModel):
    """创建用户请求。租户不由请求体指定（由认证上下文决定），
    故禁止未声明的额外字段（如 tenant_id）以免调用方误以为可指定。"""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="User email")
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="User password (8-72 chars, bcrypt 72-byte limit)",
    )
    is_superuser: bool = Field(False, description="Superuser flag")


class AdminUpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = Field(None, description="User email")
    is_active: bool | None = Field(None, description="Active status")
    is_superuser: bool | None = Field(None, description="Superuser flag")


class AdminUpdateCurrentUserRequest(BaseModel):
    email: EmailStr | None = Field(None, description="User email")


class UserAdminResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UserAdminListResponse(BaseModel):
    items: list[UserAdminResponse]
    total: int
