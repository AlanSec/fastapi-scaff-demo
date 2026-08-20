"""刷新令牌仓储接口（领域层）"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RefreshTokenRecord:
    """刷新令牌记录（服务端状态，用于吊销）"""
    jti: str
    user_id: UUID
    expires_at: datetime
    is_revoked: bool = False


class RefreshTokenRepository(ABC):

    @abstractmethod
    async def save(self, jti: str, user_id: UUID, expires_at: datetime) -> None:
        """持久化刷新令牌（按 jti）"""
        pass

    @abstractmethod
    async def find_by_token(self, jti: str) -> Optional[RefreshTokenRecord]:
        pass

    @abstractmethod
    async def revoke(self, jti: str) -> bool:
        """吊销令牌（轮换/登出时调用）"""
        pass

    @abstractmethod
    async def delete_expired(self, now: datetime) -> int:
        """删除所有已过期的记录（防止 refresh_tokens 表无限增长），返回删除条数"""
        pass
