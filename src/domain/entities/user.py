from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


@dataclass(frozen=True, eq=True)
class User:
    id: UUID
    email: Email
    password: HashedPassword
    tenant_id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        email: Email,
        password: HashedPassword,
        tenant_id: UUID
    ) -> "User":
        now = datetime.now()
        return cls(
            id=uuid4(),
            email=email,
            password=password,
            tenant_id=tenant_id,
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now
        )
    
    def verify(self) -> "User":
        return replace(
            self,
            is_verified=True,
            updated_at=datetime.now()
        )
    
    def update_last_login(self) -> "User":
        return replace(
            self,
            last_login_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def deactivate(self) -> "User":
        return replace(
            self,
            is_active=False,
            updated_at=datetime.now()
        )
    
    def activate(self) -> "User":
        return replace(
            self,
            is_active=True,
            updated_at=datetime.now()
        )