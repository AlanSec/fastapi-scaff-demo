"""SQLModel 用户仓储实现（每次操作独立会话）"""
from typing import List, Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.persistence.database import session_scope
from src.infrastructure.persistence.sqlmodel.mappers.user_mapper import UserMapper
from src.infrastructure.persistence.sqlmodel.models.user import UserModel


class SQLModelUserRepository(UserRepository):
    """基于 SQLModel 的用户仓储实现"""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save(self, user: User) -> User:
        """保存用户（已存在则更新，否则新增）"""
        async with session_scope(self._session_factory) as session:
            existing = await session.get(UserModel, user.id)
            if existing is not None:
                model = UserMapper.apply_to_model(existing, user)
                session.add(model)
            else:
                model = UserMapper.to_model(user)
                session.add(model)
            await session.commit()
            await session.refresh(model)
            return UserMapper.to_entity(model)

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID查找用户"""
        async with session_scope(self._session_factory) as session:
            model = await session.get(UserModel, user_id)
            if model is None:
                return None
            return UserMapper.to_entity(model)

    async def find_by_email(self, email: str, tenant_id: Optional[UUID]) -> Optional[User]:
        """通过邮箱和租户ID查找用户"""
        from sqlalchemy import select
        async with session_scope(self._session_factory) as session:
            query = select(UserModel).where(UserModel.email == email)
            if tenant_id is not None:
                query = query.where(UserModel.tenant_id == tenant_id)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return UserMapper.to_entity(model)

    async def find_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """查找租户下的用户"""
        from sqlalchemy import select
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(UserModel)
                .where(UserModel.tenant_id == tenant_id)
                .offset(skip)
                .limit(limit)
            )
            models = result.scalars().all()
            return [UserMapper.to_entity(m) for m in models]

    async def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        async with session_scope(self._session_factory) as session:
            model = await session.get(UserModel, user_id)
            if model is None:
                return False
            await session.delete(model)
            await session.commit()
            return True

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        from sqlalchemy import select
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(UserModel).offset(skip).limit(limit)
            )
            models = result.scalars().all()
            return [UserMapper.to_entity(m) for m in models]

    async def find_by_reset_token(self, token: str) -> Optional[User]:
        """通过重置令牌查找用户"""
        from sqlalchemy import select
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(UserModel).where(UserModel.reset_token == token)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return UserMapper.to_entity(model)

    async def find_by_verification_token(self, token: str) -> Optional[User]:
        """通过验证令牌查找用户"""
        from sqlalchemy import select
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(UserModel).where(UserModel.verification_token == token)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return UserMapper.to_entity(model)
