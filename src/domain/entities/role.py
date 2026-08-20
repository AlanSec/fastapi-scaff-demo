from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class RoleName(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass(frozen=True, eq=True)
class Role:
    id: UUID
    name: str
    description: str
    is_active: bool
    tenant_id: UUID = field()
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, name: str, description: str, tenant_id: UUID | None = None) -> "Role":
        now = datetime.now()
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            is_active=True,
            tenant_id=tenant_id or uuid4(),
            created_at=now,
            updated_at=now
        )

    def deactivate(self) -> "Role":
        return replace(
            self,
            is_active=False,
            updated_at=datetime.now()
        )

    def activate(self) -> "Role":
        return replace(
            self,
            is_active=True,
            updated_at=datetime.now()
        )

    def update_description(self, new_description: str) -> "Role":
        return replace(
            self,
            description=new_description,
            updated_at=datetime.now()
        )

    def update_name(self, new_name: str) -> "Role":
        return replace(
            self,
            name=new_name,
            updated_at=datetime.now()
        )
