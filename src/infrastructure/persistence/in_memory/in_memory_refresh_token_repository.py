"""内存刷新令牌仓储（测试用）"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from src.domain.repositories.refresh_token_repository import (
    RefreshTokenRecord,
    RefreshTokenRepository,
)


class InMemoryRefreshTokenRepository(RefreshTokenRepository):

    def __init__(self):
        self._tokens: Dict[str, RefreshTokenRecord] = {}

    async def save(self, jti: str, user_id: UUID, expires_at: datetime) -> None:
        self._tokens[jti] = RefreshTokenRecord(
            jti=jti, user_id=user_id, expires_at=expires_at
        )

    async def find_by_token(self, jti: str) -> Optional[RefreshTokenRecord]:
        return self._tokens.get(jti)

    async def revoke(self, jti: str) -> bool:
        record = self._tokens.get(jti)
        if record is None:
            return False
        self._tokens[jti] = RefreshTokenRecord(
            jti=record.jti,
            user_id=record.user_id,
            expires_at=record.expires_at,
            is_revoked=True,
        )
        return True

    async def delete_expired(self, now: datetime) -> int:
        expired = [jti for jti, rec in self._tokens.items() if rec.expires_at < now]
        for jti in expired:
            del self._tokens[jti]
        return len(expired)
