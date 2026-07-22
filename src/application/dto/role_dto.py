from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class CreateRoleInputDTO:
    name: str
    description: str
    tenant_id: UUID


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
