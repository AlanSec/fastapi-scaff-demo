from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class AuthService(ABC):
    @abstractmethod
    async def authenticate(self, email: str, password: str, tenant_id: UUID) -> Optional[dict]:
        pass

    @abstractmethod
    async def register(self, email: str, password: str, tenant_id: UUID) -> dict:
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict:
        pass


class PermissionService(ABC):
    @abstractmethod
    async def check_permission(self, user_id: UUID, resource: str, action: str) -> bool:
        pass

    @abstractmethod
    async def get_user_permissions(self, user_id: UUID) -> list[str]:
        pass

    @abstractmethod
    async def assign_role(self, user_id: UUID, role_id: UUID) -> bool:
        pass

    @abstractmethod
    async def revoke_role(self, user_id: UUID, role_id: UUID) -> bool:
        pass
