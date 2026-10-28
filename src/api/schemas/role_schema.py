"""Role schemas"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleCreateRequest(BaseModel):
    """创建角色请求。租户不由请求体指定（由认证上下文决定），
    故禁止未声明的额外字段（如 tenant_id）以免调用方误以为可指定。"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Role name")
    description: str = Field(..., description="Role description")


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Role name")
    description: str | None = Field(None, description="Role description")


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str
    is_active: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: list[RoleResponse]
    total: int
