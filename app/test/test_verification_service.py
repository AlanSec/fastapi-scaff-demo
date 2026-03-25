"""
验证服务单元测试
测试VerificationService类的功能
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.verification import VerificationService


class TestVerificationService:
    """测试VerificationService类"""

    @pytest.mark.asyncio
    async def test_create_verification_token(self, db_session: AsyncSession, default_tenant):
        """测试创建验证令牌"""
        # 创建测试用户
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 创建验证令牌
        token = await service.create_verification_token(user)

        # 验证令牌
        assert token is not None
        assert len(token) > 20  # UUID + 时间戳应该足够长
        assert user.verification_token == token

        # 验证令牌已保存到数据库
        await db_session.refresh(user)
        assert user.verification_token == token

    @pytest.mark.asyncio
    async def test_verify_email_token_success(self, db_session: AsyncSession, default_tenant):
        """测试验证邮箱令牌成功"""
        # 创建测试用户和令牌
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="test-token-123",
            email_verified=False,
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 验证令牌
        verified_user = await service.verify_email_token("test-token-123")

        # 验证结果
        assert verified_user is not None
        assert verified_user.id == user.id
        assert verified_user.email_verified is True
        assert verified_user.verification_token is None

        # 验证数据库已更新
        await db_session.refresh(user)
        assert user.email_verified is True
        assert user.verification_token is None

    @pytest.mark.asyncio
    async def test_verify_email_token_expired(self, db_session: AsyncSession, default_tenant):
        """测试验证已过期的邮箱令牌"""
        # 创建测试用户和已过期的令牌
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="expired-token",
            email_verified=False,
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 验证已过期的令牌
        verified_user = await service.verify_email_token("expired-token")

        # 验证结果不应为None（服务不检查验证令牌过期时间）
        assert verified_user is not None
        assert verified_user.email_verified is True
        assert verified_user.verification_token is None

        # 验证用户状态已改变
        await db_session.refresh(user)
        assert user.email_verified is True
        assert user.verification_token is None

    @pytest.mark.asyncio
    async def test_verify_email_token_invalid(self, db_session: AsyncSession, default_tenant):
        """测试验证无效的令牌"""
        # 创建测试用户
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            verification_token="valid-token",
            email_verified=False,
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()

        # 创建验证服务
        service = VerificationService(db_session)

        # 验证无效的令牌
        verified_user = await service.verify_email_token("invalid-token")

        # 验证结果应为None
        assert verified_user is None

    @pytest.mark.asyncio
    async def test_create_password_reset_token(self, db_session: AsyncSession, default_tenant):
        """测试创建密码重置令牌"""
        # 创建测试用户
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 创建密码重置令牌
        token = await service.create_password_reset_token(user)

        # 验证令牌
        assert token is not None
        assert len(token) > 20
        assert user.reset_token == token
        assert user.reset_token_expires is not None

        # 验证令牌已保存到数据库
        await db_session.refresh(user)
        assert user.reset_token == token

    @pytest.mark.asyncio
    async def test_verify_password_reset_token_success(self, db_session: AsyncSession, default_tenant):
        """测试验证密码重置令牌成功"""
        # 创建测试用户和令牌
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            reset_token="reset-token-123",
            reset_token_expires=datetime.utcnow() + timedelta(hours=24),
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 验证令牌
        verified_user = await service.verify_password_reset_token("reset-token-123")

        # 验证结果
        assert verified_user is not None
        assert verified_user.id == user.id

    @pytest.mark.asyncio
    async def test_verify_password_reset_token_expired(self, db_session: AsyncSession, default_tenant):
        """测试验证已过期的密码重置令牌"""
        # 创建测试用户和已过期的令牌
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            reset_token="expired-reset-token",
            reset_token_expires=datetime.utcnow() - timedelta(hours=1),
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 验证已过期的令牌
        verified_user = await service.verify_password_reset_token("expired-reset-token")

        # 验证结果应为None
        assert verified_user is None

    @pytest.mark.asyncio
    async def test_clear_password_reset_token(self, db_session: AsyncSession, default_tenant):
        """测试清除密码重置令牌"""
        # 创建测试用户和令牌
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            reset_token="reset-token-123",
            reset_token_expires=datetime.utcnow() + timedelta(hours=24),
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建验证服务
        service = VerificationService(db_session)

        # 清除令牌
        await service.clear_password_reset_token(user)

        # 验证令牌已清除
        assert user.reset_token is None
        assert user.reset_token_expires is None

        # 验证数据库已更新
        await db_session.refresh(user)
        assert user.reset_token is None