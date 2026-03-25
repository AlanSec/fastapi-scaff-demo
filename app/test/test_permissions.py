"""
权限服务单元测试
测试PermissionChecker类的功能
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.utils.permissions import PermissionChecker


class TestPermissionChecker:
    """测试PermissionChecker类"""

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, db_session: AsyncSession, default_tenant):
        """测试获取用户权限"""
        # 创建测试用户
        user = User(
            email="permuser@example.com",
            username="permuser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建角色和权限
        role = Role(name="test-role", description="测试角色", tenant_id=default_tenant.id)
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        permission = Permission(code="test:read", name="测试读取权限", description="测试权限")
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)

        # 关联用户和角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)

        # 关联角色和权限
        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        db_session.add(role_permission)

        await db_session.commit()

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 获取用户权限
        permissions = await checker.get_user_permissions(user.id)

        # 验证结果
        assert len(permissions) == 1
        assert "test:read" in permissions

    @pytest.mark.asyncio
    async def test_get_user_permissions_empty(self, db_session: AsyncSession, default_tenant):
        """测试获取无权限用户的权限"""
        # 创建测试用户（无角色关联）
        user = User(
            email="nopermuser@example.com",
            username="nopermuser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 获取用户权限
        permissions = await checker.get_user_permissions(user.id)

        # 验证结果为空
        assert len(permissions) == 0

    @pytest.mark.asyncio
    async def test_get_user_roles(self, db_session: AsyncSession, default_tenant):
        """测试获取用户角色"""
        # 创建测试用户
        user = User(
            email="roleuser@example.com",
            username="roleuser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建角色
        role = Role(name="user-role", description="用户角色", tenant_id=default_tenant.id)
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        # 关联用户和角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 获取用户角色
        roles = await checker.get_user_roles(user.id)

        # 验证结果
        assert len(roles) == 1
        assert "user-role" in roles

    @pytest.mark.asyncio
    async def test_user_has_permission_success(self, db_session: AsyncSession, default_tenant):
        """测试用户有权限"""
        # 创建测试用户
        user = User(
            email="hasperm@example.com",
            username="hasperm",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建角色和权限
        role = Role(name="has-role", description="有权限角色", tenant_id=default_tenant.id)
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        permission = Permission(code="document:read", name="文档读取", description="读取文档")
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)

        # 关联用户和角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)

        # 关联角色和权限
        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        db_session.add(role_permission)

        await db_session.commit()

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 检查用户是否有权限
        has_perm = await checker.user_has_permission(user.id, "document:read")

        # 验证结果
        assert has_perm is True

    @pytest.mark.asyncio
    async def test_user_has_permission_false(self, db_session: AsyncSession, default_tenant):
        """测试用户无权限"""
        # 创建测试用户
        user = User(
            email="nohasperm@example.com",
            username="nohasperm",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 检查用户是否有不存在的权限
        has_perm = await checker.user_has_permission(user.id, "nonexistent:permission")

        # 验证结果
        assert has_perm is False

    @pytest.mark.asyncio
    async def test_superuser_has_all_permissions(self, db_session: AsyncSession, default_tenant):
        """测试超级用户拥有所有权限"""
        # 创建超级用户
        superuser = User(
            email="super@example.com",
            username="superuser",
            hashed_password="hashed_password",
            is_superuser=True,
            tenant_id=default_tenant.id
        )
        db_session.add(superuser)
        await db_session.commit()
        await db_session.refresh(superuser)

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 检查超级用户是否有任意权限
        has_perm = await checker.user_has_permission(superuser.id, "any:permission")

        # 验证结果：超级用户应有所有权限
        assert has_perm is True

    @pytest.mark.asyncio
    async def test_user_has_role_success(self, db_session: AsyncSession, default_tenant):
        """测试用户有角色"""
        # 创建测试用户
        user = User(
            email="hasrole@example.com",
            username="hasrole",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建角色
        role = Role(name="editor", description="编辑者", tenant_id=default_tenant.id)
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        # 关联用户和角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 检查用户是否有角色
        has_role = await checker.user_has_role(user.id, "editor")

        # 验证结果
        assert has_role is True

    @pytest.mark.asyncio
    async def test_user_has_role_false(self, db_session: AsyncSession, default_tenant):
        """测试用户无角色"""
        # 创建测试用户
        user = User(
            email="norole@example.com",
            username="norole",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 检查用户是否有不存在的角色
        has_role = await checker.user_has_role(user.id, "nonexistent-role")

        # 验证结果
        assert has_role is False

    @pytest.mark.asyncio
    async def test_multiple_roles_and_permissions(self, db_session: AsyncSession, default_tenant):
        """测试用户有多个角色和权限"""
        # 创建测试用户
        user = User(
            email="multi@example.com",
            username="multiuser",
            hashed_password="hashed_password",
            tenant_id=default_tenant.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 创建两个角色
        role1 = Role(name="writer", description="写作者", tenant_id=default_tenant.id)
        role2 = Role(name="reviewer", description="审核者", tenant_id=default_tenant.id)
        db_session.add_all([role1, role2])
        await db_session.commit()
        await db_session.refresh(role1)
        await db_session.refresh(role2)

        # 创建三个权限
        perm1 = Permission(code="article:write", name="写文章", description="撰写文章")
        perm2 = Permission(code="article:review", name="审核文章", description="审核文章")
        perm3 = Permission(code="article:publish", name="发布文章", description="发布文章")
        db_session.add_all([perm1, perm2, perm3])
        await db_session.commit()

        # 关联用户和两个角色
        user_role1 = UserRole(user_id=user.id, role_id=role1.id)
        user_role2 = UserRole(user_id=user.id, role_id=role2.id)
        db_session.add_all([user_role1, user_role2])

        # 关联角色1和权限1
        role_perm1 = RolePermission(role_id=role1.id, permission_id=perm1.id)
        # 关联角色2和权限2、权限3
        role_perm2 = RolePermission(role_id=role2.id, permission_id=perm2.id)
        role_perm3 = RolePermission(role_id=role2.id, permission_id=perm3.id)
        db_session.add_all([role_perm1, role_perm2, role_perm3])

        await db_session.commit()

        # 创建权限检查器
        checker = PermissionChecker(db_session)

        # 获取用户权限
        permissions = await checker.get_user_permissions(user.id)

        # 验证结果：应该有3个权限
        assert len(permissions) == 3
        assert "article:write" in permissions
        assert "article:review" in permissions
        assert "article:publish" in permissions

        # 获取用户角色
        roles = await checker.get_user_roles(user.id)
        assert len(roles) == 2
        assert "writer" in roles
        assert "reviewer" in roles