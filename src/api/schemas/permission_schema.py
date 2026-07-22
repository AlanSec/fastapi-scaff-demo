from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class PermissionCreateRequest(BaseModel):
    action: str = Field(..., description="Permission action (create, read, update, delete)")
    resource: str = Field(..., description="Resource name (user, tenant, role, permission)")
    description: str = Field(..., description="Permission description")


class PermissionUpdateRequest(BaseModel):
    description: str | None = Field(None, description="Permission description")


class PermissionResponse(BaseModel):
    id: UUID
    action: str
    resource: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PermissionListResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
