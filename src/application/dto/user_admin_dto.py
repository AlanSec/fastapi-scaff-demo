from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class AdminCreateUserInputDTO:
    email: str
    password: str
    tenant_id: UUID
    username: str | None = None
    is_superuser: bool = False


@dataclass(frozen=True)
class AdminUpdateUserInputDTO:
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    tenant_id: UUID | None = None


@dataclass(frozen=True)
class UserAdminOutputDTO:
    id: UUID
    email: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


@dataclass(frozen=True)
class AdminUpdateCurrentUserInputDTO:
    email: str | None = None


@dataclass(frozen=True)
class AssignRoleInputDTO:
    user_id: UUID
    role_id: UUID


@dataclass(frozen=True)
class AssignPermissionInputDTO:
    role_id: UUID
    permission_id: UUID
    tenant_id: UUID
