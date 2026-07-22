from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class CreatePermissionInputDTO:
    action: str
    resource: str
    description: str


@dataclass(frozen=True)
class UpdatePermissionInputDTO:
    description: str | None = None


@dataclass(frozen=True)
class PermissionOutputDTO:
    id: UUID
    action: str
    resource: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
