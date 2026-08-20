from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateTenantInputDTO:
    name: str
    domain: str


@dataclass(frozen=True)
class UpdateTenantInputDTO:
    name: str | None = None
    domain: str | None = None


@dataclass(frozen=True)
class TenantOutputDTO:
    id: UUID
    name: str
    domain: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
