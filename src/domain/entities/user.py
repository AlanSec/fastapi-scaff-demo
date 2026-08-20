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
    is_superuser: bool = False
    reset_token: Optional[str] = None
    reset_token_expires_at: Optional[datetime] = None
    verification_token: Optional[str] = None

    @classmethod
    def create(
        cls,
        email: Email,
        password: HashedPassword,
        tenant_id: UUID,
        is_superuser: bool = False,
    ) -> "User":
        now = datetime.now()
        return cls(
            id=uuid4(),
            email=email,
            password=password,
            tenant_id=tenant_id,
            is_active=True,
            is_verified=False,
            is_superuser=is_superuser,
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

    def with_reset_token(self, token: str, expires_at: datetime) -> "User":
        return replace(
            self,
            reset_token=token,
            reset_token_expires_at=expires_at,
            updated_at=datetime.now()
        )

    def clear_reset_token(self) -> "User":
        return replace(
            self,
            reset_token=None,
            reset_token_expires_at=None,
            updated_at=datetime.now()
        )

    def with_verification_token(self, token: str) -> "User":
        return replace(
            self,
            verification_token=token,
            updated_at=datetime.now()
        )

    def clear_verification_token(self) -> "User":
        return replace(
            self,
            verification_token=None,
            updated_at=datetime.now()
        )
