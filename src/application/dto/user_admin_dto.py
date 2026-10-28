from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class AdminCreateUserInputDTO:
    email: str
    password: str
    # 注意：无 tenant_id 字段——用户所属租户由认证上下文决定（UseCase 显式入参）
    is_superuser: bool = False


@dataclass(frozen=True)
class AdminUpdateUserInputDTO:
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


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
