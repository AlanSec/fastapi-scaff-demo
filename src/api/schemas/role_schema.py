from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoleCreateRequest(BaseModel):
    name: str = Field(..., description="Role name")
    description: str = Field(..., description="Role description")
    tenant_id: UUID = Field(..., description="Tenant ID")


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
