import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine, init_db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_first_tenant_and_admin() -> None:
    """创建第一个租户和管理员用户"""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 检查是否已存在租户
        result = await session.execute(select(Tenant).where(Tenant.name == "默认租户"))
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.info("创建默认租户")
            tenant = Tenant(name="默认租户", description="系统默认租户")
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)

        # 检查是否已存在管理员用户
        result = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        user = result.scalar_one_or_none()

        user_created = False
        if not user:
            logger.info("创建管理员用户")
            user = User(
                email=settings.ADMIN_EMAIL,
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_superuser=settings.ADMIN_IS_SUPERUSER,
                tenant_id=tenant.id,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            user_created = True
        else:
            logger.info("管理员用户已存在")

        # 为管理员用户分配admin角色
        logger.info("为管理员用户分配admin角色")

        # 查找admin角色
        role_result = await session.execute(
            select(Role).where(
                Role.name == "admin",
                Role.tenant_id == tenant.id,
                Role.is_active == True
            )
        )
        admin_role = role_result.scalar_one_or_none()

        if admin_role:
            # 检查是否已存在关联
            existing_assoc_result = await session.execute(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == admin_role.id
                )
            )
            existing_assoc = existing_assoc_result.scalar_one_or_none()

            if not existing_assoc:
                # 创建用户-角色关联
                user_role_assoc = UserRole(
                    user_id=user.id,
                    role_id=admin_role.id,
                    is_active=True
                )
                session.add(user_role_assoc)
                await session.commit()
                logger.info(f"管理员用户已分配admin角色 (用户ID: {user.id}, 角色ID: {admin_role.id})")
            else:
                logger.info("管理员用户已拥有admin角色，跳过分配")
        else:
            logger.warning("未找到admin角色，管理员用户将无法访问权限控制功能")


async def init() -> None:
    logger.info("初始化数据库")
    await init_db()
    logger.info("创建初始数据")
    await create_first_tenant_and_admin()
    logger.info("初始化完成")


def main() -> None:
    logger.info("创建初始数据")
    asyncio.run(init())
    logger.info("初始数据创建完成")


if __name__ == "__main__":
    main()
