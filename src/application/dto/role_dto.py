from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateRoleInputDTO:
    name: str
    description: str
    # 注意：无 tenant_id 字段——角色所属租户由认证上下文决定（UseCase 显式入参）


@dataclass(frozen=True)
class UpdateRoleInputDTO:
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class RoleOutputDTO:
    id: UUID
    name: str
    description: str
    is_active: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
