from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminCreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    tenant_id: UUID = Field(..., description="Tenant ID")
    is_superuser: bool = Field(False, description="Superuser flag")


class AdminUpdateUserRequest(BaseModel):
    email: EmailStr | None = Field(None, description="User email")
    is_active: bool | None = Field(None, description="Active status")
    is_superuser: bool | None = Field(None, description="Superuser flag")
    tenant_id: UUID | None = Field(None, description="Tenant ID")


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
