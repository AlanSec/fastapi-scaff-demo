from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: UUID, tenant_id: UUID) -> Optional[User]:
        """按 ID 查询用户，必须限定在指定租户内（跨租户返回 None）"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: Optional[UUID]) -> Optional[User]:
        """按邮箱查询用户；tenant_id 为 None 时跨租户查找（取首个匹配，供 forgot/resend 使用）"""
        pass

    @abstractmethod
    async def find_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """查询指定租户下的用户（分页）"""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID, tenant_id: UUID) -> bool:
        """删除指定租户内的用户（跨租户返回 False）"""
        pass

    @abstractmethod
    async def find_by_reset_token(self, token: str) -> Optional[User]:
        pass

    @abstractmethod
    async def find_by_verification_token(self, token: str) -> Optional[User]:
        pass
