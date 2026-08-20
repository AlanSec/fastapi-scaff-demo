"""SQLModel 刷新令牌仓储实现"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from src.domain.repositories.refresh_token_repository import (
    RefreshTokenRecord,
    RefreshTokenRepository,
)
from src.infrastructure.persistence.database import session_scope
from src.infrastructure.persistence.sqlmodel.models.refresh_token import RefreshTokenModel


class SQLModelRefreshTokenRepository(RefreshTokenRepository):

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save(self, jti: str, user_id: UUID, expires_at: datetime) -> None:
        async with session_scope(self._session_factory) as session:
            # 顺带清理已过期记录，避免表无限增长（每次登录/轮换都会触发）
            await session.execute(
                delete(RefreshTokenModel).where(
                    RefreshTokenModel.expires_at < datetime.now(timezone.utc)
                )
            )
            existing = await session.execute(
                select(RefreshTokenModel).where(RefreshTokenModel.token == jti)
            )
            model = existing.scalar_one_or_none()
            if model is not None:
                model.is_revoked = False
                model.expires_at = expires_at
                session.add(model)
            else:
                session.add(RefreshTokenModel(
                    token=jti,
                    user_id=user_id,
                    expires_at=expires_at,
                ))
            await session.commit()

    async def find_by_token(self, jti: str) -> Optional[RefreshTokenRecord]:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RefreshTokenModel).where(RefreshTokenModel.token == jti)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return RefreshTokenRecord(
                jti=model.token,
                user_id=model.user_id,
                expires_at=model.expires_at,
                is_revoked=model.is_revoked,
            )

    async def revoke(self, jti: str) -> bool:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RefreshTokenModel).where(RefreshTokenModel.token == jti)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return False
            model.is_revoked = True
            session.add(model)
            await session.commit()
            return True

    async def delete_expired(self, now: datetime) -> int:
        """删除所有已过期的记录，返回删除条数"""
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < now)
            )
            await session.commit()
            return result.rowcount or 0
