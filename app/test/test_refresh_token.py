"""
刷新令牌测试
测试刷新令牌的创建、验证和轮换功能
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.services.auth import create_user_token, refresh_access_token
from app.core.config import settings


class TestRefreshToken:
    """测试刷新令牌功能"""

    @pytest.mark.asyncio
    async def test_create_user_token_returns_both_tokens(self, db_session: AsyncSession, default_tenant):
        """测试登录时同时返回访问令牌和刷新令牌"""
        # 创建测试用户
        user = User(
            email="refreshtest@example.com",
            username="refreshtest",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建令牌
        token_data = await create_user_token(user.id, db_session)

        # 验证返回的令牌
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_stored_in_database(self, db_session: AsyncSession, default_tenant):
        """测试刷新令牌存储在数据库中"""
        # 创建测试用户
        user = User(
            email="tokenstore@example.com",
            username="tokenstore",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建令牌
        token_data = await create_user_token(user.id, db_session)

        # 验证刷新令牌已存储
        from sqlalchemy import select
        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == token_data["refresh_token"])
        )
        refresh_token = result.scalar_one_or_none()

        assert refresh_token is not None
        assert refresh_token.user_id == user.id
        assert refresh_token.is_revoked is False
        assert refresh_token.expires_at > datetime.now()

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, db_session: AsyncSession, default_tenant):
        """测试使用刷新令牌获取新令牌"""
        import asyncio

        # 创建测试用户
        user = User(
            email="refreshsuccess@example.com",
            username="refreshsuccess",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建初始令牌
        initial_token = await create_user_token(user.id, db_session)

        # 等待一小段时间，确保新令牌有不同的过期时间
        await asyncio.sleep(0.1)

        # 使用刷新令牌获取新令牌
        new_token = await refresh_access_token(initial_token["refresh_token"], db_session)

        # 验证新令牌
        assert "access_token" in new_token
        assert "refresh_token" in new_token
        # 验证刷新令牌不同（令牌轮换）
        assert new_token["refresh_token"] != initial_token["refresh_token"]

    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, db_session: AsyncSession, default_tenant):
        """测试刷新令牌轮换（旧令牌失效）"""
        # 创建测试用户
        user = User(
            email="rotation@example.com",
            username="rotation",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建初始令牌
        initial_token = await create_user_token(user.id, db_session)
        old_refresh_token = initial_token["refresh_token"]

        # 使用刷新令牌获取新令牌
        await refresh_access_token(old_refresh_token, db_session)

        # 验证旧的刷新令牌已失效
        from sqlalchemy import select
        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == old_refresh_token)
        )
        old_token_record = result.scalar_one_or_none()

        assert old_token_record is not None
        assert old_token_record.is_revoked is True

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(self, db_session: AsyncSession):
        """测试使用无效的刷新令牌"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token("invalid_token", db_session)

        assert exc_info.value.status_code == 401
        assert "无效的刷新令牌" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, db_session: AsyncSession, default_tenant):
        """测试过期的刷新令牌"""
        from fastapi import HTTPException

        # 创建测试用户
        user = User(
            email="expired@example.com",
            username="expired",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建过期的刷新令牌
        expired_token = RefreshToken(
            user_id=user.id,
            token="expired_token_123",
            expires_at=datetime.now() - timedelta(days=1),  # 已过期
            is_revoked=False
        )
        db_session.add(expired_token)
        await db_session.commit()

        # 尝试使用过期的刷新令牌
        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token("expired_token_123", db_session)

        assert exc_info.value.status_code == 401
        assert "刷新令牌已过期" in exc_info.value.detail
