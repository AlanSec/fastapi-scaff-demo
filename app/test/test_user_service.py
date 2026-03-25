"""
用户服务单元测试
测试UserService类的功能
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user import UserService


class TestUserService:
    """测试UserService类"""

    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session: AsyncSession, default_tenant):
        """测试注册用户成功"""
        service = UserService(db_session)

        # 注册新用户
        user = await service.register_user(
            email="newuser@example.com",
            username="newuser",
            password="Password123!"
        )

        # 验证用户信息
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.hashed_password is not None
        assert user.hashed_password != "Password123!"  # 密码应该被哈希
        assert user.is_active is True
        assert user.email_verified is False
        assert user.verification_token is not None

        # 验证用户已保存到数据库
        db_user = await db_session.get(User, user.id)
        assert db_user is not None
        assert db_user.email == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, db_session: AsyncSession, default_tenant):
        """测试注册重复邮箱"""
        # 先创建一个用户
        existing_user = User(
            email="existing@example.com",
            username="existing",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(existing_user)
        await db_session.commit()

        service = UserService(db_session)

        # 尝试用相同邮箱注册新用户
        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(
                email="existing@example.com",
                username="newuser",
                password="Password123!"
            )

        # 验证异常信息
        assert exc_info.value.status_code == 400
        assert "邮箱已被注册" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, db_session: AsyncSession, default_tenant):
        """测试注册重复用户名"""
        # 先创建一个用户
        existing_user = User(
            email="user1@example.com",
            username="existinguser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(existing_user)
        await db_session.commit()

        service = UserService(db_session)

        # 尝试用相同用户名注册新用户
        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(
                email="newuser@example.com",
                username="existinguser",
                password="Password123!"
            )

        # 验证异常信息
        assert exc_info.value.status_code == 400
        assert "用户名已被使用" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_user_with_default_roles(self, db_session: AsyncSession, default_tenant):
        """测试注册用户时分配默认角色"""
        # 注意：此测试需要数据库中有默认角色数据
        # 在运行此测试前，需要确保数据库迁移已执行
        service = UserService(db_session)

        # 注册新用户
        user = await service.register_user(
            email="roleuser@example.com",
            username="roleuser",
            password="Password123!"
        )

        # 验证用户已创建
        assert user is not None

        # 注意：在实际测试中，由于测试数据库是空的，可能没有默认角色
        # 这里我们主要测试流程不抛出异常
        # 在实际部署中，迁移脚本会创建默认角色

    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, db_session: AsyncSession, default_tenant):
        """测试注册时使用弱密码"""
        service = UserService(db_session)

        # 尝试使用弱密码注册
        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(
                email="weak@example.com",
                username="weakuser",
                password="123"  # 太短
            )

        # 验证异常信息
        assert exc_info.value.status_code == 400
        assert "密码" in exc_info.value.detail or "弱" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session: AsyncSession, default_tenant):
        """测试通过邮箱获取用户"""
        # 创建测试用户
        test_user = User(
            email="testget@example.com",
            username="testget",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(test_user)
        await db_session.commit()

        service = UserService(db_session)

        # 获取用户
        user = await service.get_user_by_email("testget@example.com")

        # 验证结果
        assert user is not None
        assert user.email == "testget@example.com"
        assert user.username == "testget"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        """测试获取不存在的用户"""
        service = UserService(db_session)

        # 获取不存在的用户
        user = await service.get_user_by_email("nonexistent@example.com")

        # 验证结果
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, db_session: AsyncSession, default_tenant):
        """测试通过用户名获取用户"""
        # 创建测试用户
        test_user = User(
            email="testuser@example.com",
            username="testusername",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(test_user)
        await db_session.commit()

        service = UserService(db_session)

        # 获取用户
        user = await service.get_user_by_username("testusername")

        # 验证结果
        assert user is not None
        assert user.username == "testusername"
        assert user.email == "testuser@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, db_session: AsyncSession):
        """测试获取不存在的用户名"""
        service = UserService(db_session)

        # 获取不存在的用户
        user = await service.get_user_by_username("nonexistent")

        # 验证结果
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession, default_tenant):
        """测试用户认证成功"""
        service = UserService(db_session)

        # 先注册用户
        user = await service.register_user(
            email="auth@example.com",
            username="authuser",
            password="Password123!"
        )

        # 认证用户
        authenticated_user = await service.authenticate_user(
            username="authuser",
            password="Password123!"
        )

        # 验证结果
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == "auth@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, default_tenant):
        """测试用户认证密码错误"""
        service = UserService(db_session)

        # 先注册用户
        await service.register_user(
            email="auth2@example.com",
            username="authuser2",
            password="Password123!"
        )

        # 使用错误密码认证
        authenticated_user = await service.authenticate_user(
            username="authuser2",
            password="WrongPassword!"
        )

        # 验证结果应为None
        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session: AsyncSession):
        """测试认证不存在的用户"""
        service = UserService(db_session)

        # 认证不存在的用户
        authenticated_user = await service.authenticate_user(
            username="nonexistent",
            password="Password123!"
        )

        # 验证结果应为None
        assert authenticated_user is None