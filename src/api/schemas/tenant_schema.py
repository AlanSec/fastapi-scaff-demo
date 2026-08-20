from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    name: str = Field(..., description="Tenant name")
    domain: str = Field(..., description="Tenant domain")


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Tenant name")
    domain: str | None = Field(None, description="Tenant domain")


class TenantResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
