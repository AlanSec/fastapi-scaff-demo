from dataclasses import dataclass, replace
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
    name: RoleName
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, name: RoleName, description: str) -> "Role":
        now = datetime.now()
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            is_active=True,
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