"""
登录限制测试
测试登录失败次数限制和账户锁定功能
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.models.user import User
from app.services.auth import authenticate_user
from app.core.config import settings
from app.core.security import get_password_hash


class TestLoginLimit:
    """测试登录限制功能"""

    @pytest.mark.asyncio
    async def test_failed_login_increments_counter(self, db_session: AsyncSession, default_tenant):
        """测试登录失败增加计数器"""
        # 创建测试用户
        user = User(
            email="faillimit@example.com",
            username="faillimit",
            hashed_password=get_password_hash("correct_password"),
            tenant_id=default_tenant.id,
            failed_login_attempts=0
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 尝试使用错误密码登录
        result = await authenticate_user("faillimit", "wrong_password", db_session)

        # 验证登录失败
        assert result is None

        # 刷新用户数据
        await db_session.refresh(user)

        # 验证失败计数增加
        assert user.failed_login_attempts == 1

    @pytest.mark.asyncio
    async def test_successful_login_resets_counter(self, db_session: AsyncSession, default_tenant):
        """测试成功登录重置计数器"""
        # 创建测试用户（已有失败记录）
        user = User(
            email="resetcounter@example.com",
            username="resetcounter",
            hashed_password=get_password_hash("correct_password"),
            tenant_id=default_tenant.id,
            failed_login_attempts=2
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 使用正确密码登录
        result = await authenticate_user("resetcounter", "correct_password", db_session)

        # 验证登录成功
        assert result is not None
        assert result.id == user.id

        # 刷新用户数据
        await db_session.refresh(user)

        # 验证失败计数重置
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    @pytest.mark.asyncio
    async def test_account_lockout_after_max_attempts(self, db_session: AsyncSession, default_tenant):
        """测试达到最大尝试次数后锁定账户"""
        # 创建测试用户（接近锁定阈值）
        user = User(
            email="lockout@example.com",
            username="lockout",
            hashed_password=get_password_hash("correct_password"),
            tenant_id=default_tenant.id,
            failed_login_attempts=settings.MAX_LOGIN_ATTEMPTS - 1
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 再次尝试错误密码登录（应该触发锁定）
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_user("lockout", "wrong_password", db_session)

        # 验证返回锁定错误
        assert exc_info.value.status_code == 423
        assert "登录失败次数过多" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_locked_account_rejects_login(self, db_session: AsyncSession, default_tenant):
        """测试被锁定的账户拒绝登录"""
        # 创建被锁定的用户
        locked_until = datetime.now() + timedelta(minutes=30)
        user = User(
            email="locked@example.com",
            username="locked",
            hashed_password=get_password_hash("correct_password"),
            tenant_id=default_tenant.id,
            failed_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
            locked_until=locked_until
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 尝试登录被锁定的账户
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_user("locked", "correct_password", db_session)

        # 验证返回锁定错误
        assert exc_info.value.status_code == 423
        assert "账户已被锁定" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_unlocked_account_can_login(self, db_session: AsyncSession, default_tenant):
        """测试锁定过期后可以登录"""
        # 创建锁定已过期的用户
        locked_until = datetime.now() - timedelta(minutes=1)  # 锁定已过期
        user = User(
            email="unlocked@example.com",
            username="unlocked",
            hashed_password=get_password_hash("correct_password"),
            tenant_id=default_tenant.id,
            failed_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
            locked_until=locked_until
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 尝试登录（锁定已过期）
        result = await authenticate_user("unlocked", "correct_password", db_session)

        # 验证登录成功
        assert result is not None
        assert result.id == user.id

        # 刷新用户数据
        await db_session.refresh(user)

        # 验证锁定状态被清除
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestLoginLimitAPI:
    """测试登录限制API端点"""

    def test_login_with_wrong_password(self, test_client: TestClient):
        """测试使用错误密码登录"""
        # 先注册用户
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "username": "logintest",
                "password": "CorrectPassword123!"
            }
        )

        # 尝试使用错误密码登录
        response = test_client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "logintest",
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_with_correct_password(self, test_client: TestClient):
        """测试使用正确密码登录"""
        # 先注册用户
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest2@example.com",
                "username": "logintest2",
                "password": "CorrectPassword123!"
            }
        )

        # 使用正确密码登录
        response = test_client.post(
            "/api/v1/auth/login/json",
            json={
                "username": "logintest2",
                "password": "CorrectPassword123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
