import uuid

from fastapi import HTTPException,status
from sqlalchemy.future import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models import Tenant, User
from app.schemas.tenant import TenantCreate, TenantUpdate
from uuid import UUID


class TenantsServices:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, tenant_in: TenantCreate) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.name == tenant_in.name))
        tenant = result.scalar_one_or_none()
        if tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该租户名称已存在",
            )

        # 创建新租户
        db_tenant = Tenant(
            name=tenant_in.name,
            description=tenant_in.description,
            is_active=tenant_in.is_active,
        )
        self.db.add(db_tenant)
        await self.db.commit()
        await self.db.refresh(db_tenant)
        return db_tenant

    async def read_tenant_by_id(self, tenant_id: str, current_user: User,skip: int = 0, limit: int = 100) -> Tenant:

        # 处理特殊值 'me'，表示当前用户的租户
        if tenant_id == "me":
            tenant_id = str(current_user.tenant_id)

        # 验证 tenant_id 是否为有效的 UUID
        try:
            uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的租户ID格式",
            )

        # 非超级管理员只能查看自己所属的租户
        if not current_user.is_superuser and str(current_user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该租户信息",
            )

        # 查询租户
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id).offset(skip).limit(limit))
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在",
            )

        return tenant

    async def update_tenant(self, tenant_id: str, tenant_in: TenantUpdate) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="租户不存在",
            )

        if tenant_in.name is not None:
            # 检查新名称是否与其他租户冲突
            if tenant_in.name != tenant.name:
                name_check = await self.db.execute(select(Tenant).where(Tenant.name == tenant_in.name))
                existing = name_check.scalar_one_or_none()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="该租户名称已存在",
                    )
            tenant.name = tenant_in.name

        if tenant_in.description is not None:
            tenant.description = tenant_in.description

        if tenant_in.is_active is not None:
            tenant.is_active = tenant_in.is_active

        await  self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def delete_tenant(self, tenant_id: str) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该租户不存在",
            )
        await self.db.delete(tenant)
        await self.db.commit()
        return tenant

    async def read_tenant_users(self, skip: int = 0, limit: int = 100):
        try:
            # 使用SQLAlchemy 2.0语法
            result = await self.db.execute(select(Tenant).offset(skip).limit(limit))
            tenants = result.scalars().all()
            return tenants
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询租户列表失败: {str(e)}"
            )