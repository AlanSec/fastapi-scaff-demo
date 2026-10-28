from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True, eq=True)
class Role:
    id: UUID
    name: str
    description: str
    is_active: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, name: str, description: str, tenant_id: UUID) -> "Role":
        """创建角色。tenant_id 必填：角色必须归属于一个真实存在的租户。"""
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            is_active=True,
            tenant_id=tenant_id,
            created_at=now,
            updated_at=now
        )

    def deactivate(self) -> "Role":
        return replace(
            self,
            is_active=False,
            updated_at=datetime.now(timezone.utc)
        )

    def activate(self) -> "Role":
        return replace(
            self,
            is_active=True,
            updated_at=datetime.now(timezone.utc)
        )

    def update_description(self, new_description: str) -> "Role":
        return replace(
            self,
            description=new_description,
            updated_at=datetime.now(timezone.utc)
        )

    def update_name(self, new_name: str) -> "Role":
        return replace(
            self,
            name=new_name,
            updated_at=datetime.now(timezone.utc)
        )
