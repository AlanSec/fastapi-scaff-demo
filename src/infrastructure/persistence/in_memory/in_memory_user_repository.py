"""内存用户仓储实现（测试用）"""
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    """基于内存的用户仓储实现（用于测试）"""

    def __init__(self):
        self._users: Dict[UUID, User] = {}
        self._email_index: Dict[tuple, UUID] = {}
        self._reset_tokens: Dict[str, UUID] = {}
        self._verification_tokens: Dict[str, UUID] = {}

    async def save(self, user: User) -> User:
        """保存用户（同步邮箱与 token 索引）"""
        old = self._users.get(user.id)
        if old is not None:
            if old.reset_token:
                self._reset_tokens.pop(old.reset_token, None)
            if old.verification_token:
                self._verification_tokens.pop(old.verification_token, None)

        self._users[user.id] = user
        self._email_index[(str(user.email).lower(), user.tenant_id)] = user.id

        if user.reset_token:
            self._reset_tokens[user.reset_token] = user.id
        if user.verification_token:
            self._verification_tokens[user.verification_token] = user.id
        return user

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID查找用户"""
        return self._users.get(user_id)

    async def find_by_email(self, email: str, tenant_id: Optional[UUID]) -> Optional[User]:
        """通过邮箱和租户ID查找用户"""
        if tenant_id:
            key = (email.lower(), tenant_id)
            user_id = self._email_index.get(key)
            if user_id is None:
                return None
            return self._users.get(user_id)

        for (em, _), uid in self._email_index.items():
            if em == email.lower():
                return self._users.get(uid)
        return None

    async def find_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """查找租户下的用户"""
        users = [u for u in self._users.values() if u.tenant_id == tenant_id]
        return users[skip:skip + limit]

    async def delete(self, user_id: UUID) -> bool:
        """删除用户（清理邮箱与 token 索引）"""
        if user_id not in self._users:
            return False
        user = self._users.pop(user_id)
        self._email_index.pop((str(user.email).lower(), user.tenant_id), None)
        if user.reset_token:
            self._reset_tokens.pop(user.reset_token, None)
        if user.verification_token:
            self._verification_tokens.pop(user.verification_token, None)
        return True

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        items = sorted(self._users.values(), key=lambda u: u.created_at, reverse=True)
        return items[skip:skip + limit]

    async def find_by_reset_token(self, token: str) -> Optional[User]:
        """通过重置令牌查找用户"""
        user_id = self._reset_tokens.get(token)
        if user_id is None:
            return None
        return self._users.get(user_id)

    async def find_by_verification_token(self, token: str) -> Optional[User]:
        """通过验证令牌查找用户"""
        user_id = self._verification_tokens.get(token)
        if user_id is None:
            return None
        return self._users.get(user_id)
