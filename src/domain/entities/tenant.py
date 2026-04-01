from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, eq=True)
class Tenant:
    id: UUID
    name: str
    domain: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def create(cls, name: str, domain: str) -> "Tenant":
        now = datetime.now()
        return cls(
            id=uuid4(),
            name=name,
            domain=domain,
            is_active=True,
            created_at=now,
            updated_at=now
        )
    
    def deactivate(self) -> "Tenant":
        return replace(
            self,
            is_active=False,
            updated_at=datetime.now()
        )
    
    def activate(self) -> "Tenant":
        return replace(
            self,
            is_active=True,
            updated_at=datetime.now()
        )
    
    def update_domain(self, new_domain: str) -> "Tenant":
        return replace(
            self,
            domain=new_domain,
            updated_at=datetime.now()
        )
    
    def update_name(self, new_name: str) -> "Tenant":
        return replace(
            self,
            name=new_name,
            updated_at=datetime.now()
        )