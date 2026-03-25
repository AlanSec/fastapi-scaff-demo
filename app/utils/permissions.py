from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_session
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.services.auth import get_current_user


class PermissionChecker:
    """权限检查器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """获取用户的所有权限代码

        Args:
            user_id: 用户ID

        Returns:
            List[str]: 权限代码列表
        """
        # 查询用户的所有角色
        user_roles_query = select(UserRole.role_id).where(
            UserRole.user_id == user_id,
            UserRole.is_active == True
        )
        user_roles_result = await self.db.execute(user_roles_query)
        user_role_ids = [role_id for (role_id,) in user_roles_result.all()]

        if not user_role_ids:
            return []

        # 查询这些角色的所有权限
        permissions_query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id.in_(user_role_ids),
                RolePermission.is_active == True,
                Permission.is_active == True
            )
        )
        permissions_result = await self.db.execute(permissions_query)
        permissions = [code for (code,) in permissions_result.all()]

        return permissions

    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """获取用户的所有角色名称

        Args:
            user_id: 用户ID

        Returns:
            List[str]: 角色名称列表
        """
        user_roles_query = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                Role.is_active == True
            )
        )
        user_roles_result = await self.db.execute(user_roles_query)
        roles = [name for (name,) in user_roles_result.all()]

        return roles

    async def user_has_permission(self, user_id: UUID, permission_code: str) -> bool:
        """检查用户是否有特定权限

        Args:
            user_id: 用户ID
            permission_code: 权限代码

        Returns:
            bool: 是否有权限
        """
        # 超级管理员拥有所有权限
        user_query = select(User.is_superuser).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        is_superuser = user_result.scalar_one_or_none()

        if is_superuser:
            return True

        # 检查用户权限
        permission_query = (
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                RolePermission.is_active == True,
                Permission.is_active == True,
                Permission.code == permission_code
            )
        )
        permission_result = await self.db.execute(permission_query)
        permission = permission_result.scalar_one_or_none()

        return permission is not None

    async def user_has_role(self, user_id: UUID, role_name: str) -> bool:
        """检查用户是否有特定角色

        Args:
            user_id: 用户ID
            role_name: 角色名称

        Returns:
            bool: 是否有角色
        """
        role_query = (
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                Role.is_active == True,
                Role.name == role_name
            )
        )
        role_result = await self.db.execute(role_query)
        role = role_result.scalar_one_or_none()

        return role is not None


async def get_permission_checker(db: AsyncSession = Depends(get_session)) -> PermissionChecker:
    """获取权限检查器实例"""
    return PermissionChecker(db)


# FastAPI依赖项
async def has_permission(permission_code: str):
    """权限检查依赖项

    用法：
        @app.get("/some-endpoint")
        async def some_endpoint(user = Depends(has_permission("user:read"))):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_user),
        checker: PermissionChecker = Depends(get_permission_checker)
    ) -> User:
        has_perm = await checker.user_has_permission(current_user.id, permission_code)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission_code}"
            )
        return current_user

    return permission_dependency


async def has_role(role_name: str):
    """角色检查依赖项

    用法：
        @app.get("/some-endpoint")
        async def some_endpoint(user = Depends(has_role("admin"))):
            ...
    """
    async def role_dependency(
        current_user: User = Depends(get_current_user),
        checker: PermissionChecker = Depends(get_permission_checker)
    ) -> User:
        has_role_perm = await checker.user_has_role(current_user.id, role_name)
        if not has_role_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少角色: {role_name}"
            )
        return current_user

    return role_dependency


# 常用权限检查的快捷方式
async def require_user_read(db: AsyncSession = Depends(get_session)) -> User:
    """要求用户读取权限"""
    from app.services.auth import get_current_user
    from fastapi import Request
    
    # 这个函数需要在路由中使用，通过依赖注入获取current_user
    # 此处仅为示例，实际使用时应通过Depends(get_current_user)获取用户
    checker = PermissionChecker(db)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="请使用 has_permission 依赖项进行权限检查"
    )


async def require_user_manage(db: AsyncSession = Depends(get_session)) -> User:
    """要求用户管理权限（创建、更新、删除）"""
    checker = PermissionChecker(db)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="请使用 has_permission 依赖项进行权限检查"
    )


async def require_admin_role(db: AsyncSession = Depends(get_session)) -> User:
    """要求管理员角色"""
    checker = PermissionChecker(db)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="请使用 has_role 依赖项进行角色检查"
    )