from fastapi import HTTPException,status
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.schemas.user import UserCreate, UserUpdate
from app.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_in: UserCreate)-> User:
        result = await self.db.execute(select(User).where(User.email == user_in.email))
        user = result.scalar_one_or_none()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )

        # 创建新用户
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            is_superuser=user_in.is_superuser,
            tenant_id=user_in.tenant_id,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
    async def read_users(self, user_id: str) -> List[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        users = result.scalar_one_or_none()
        return users
    async def update_user(self, user_id: str, user_in: UserUpdate) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

        if user_in.password is not None:
            hashed_password = get_password_hash(user_in.password)
            user.hashed_password = hashed_password

        if user_in.email is not None:
            user.email = user_in.email

        if user_in.username is not None:
            user.username = user_in.username

        if user_in.is_active is not None:
            user.is_active = user_in.is_active

        if user_in.is_superuser is not None:
            user.is_superuser = user_in.is_superuser

        if user_in.tenant_id is not None:
            user.tenant_id = user_in.tenant_id

        await self.db.commit()
        await self.db.refresh(user)
        return user
    async def delete_user(self, user_id: str) -> None:
        results = await self.db.execute(select(User).where(User.id == user_id))
        user = results.scalar_one_or_none()
        await self.db.delete(user)
        await self.db.commit()
        return
    async def read_user_me(self, current_user: User) -> User:
        return current_user
    async def update_user_me(self, user_in: UserUpdate, current_user: User) -> User:
        if user_in.password is not None:
            hashed_password = get_password_hash(user_in.password)
            current_user.hashed_password = hashed_password

        if user_in.email is not None:
            current_user.email = user_in.email

        if user_in.username is not None:
            current_user.username = user_in.username

        await self.db.commit()
        await self.db.refresh(current_user)
        return current_user

    async def get_users(self, skip: int = 0, limit: int = 100):
        results = await self.db.execute(select(User).offset(skip).limit(limit))
        users = results.scalars().all()
        return users

    async def register_user(self, email: str, username: str, password: str) -> User:
        """公开注册新用户

        Args:
            email: 邮箱
            username: 用户名
            password: 密码

        Returns:
            User: 新创建的用户

        Raises:
            HTTPException: 邮箱已存在或其他错误
        """
        from app.core.security import get_password_hash, verify_password
        from fastapi import HTTPException, status
        from sqlalchemy import select

        # 检查邮箱是否已存在
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )

        # 检查用户名是否已存在
        result = await self.db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用",
            )

        # 验证密码强度
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度至少为8位",
            )

        # 获取默认tenant（第一个可用的tenant）
        from app.models.tenant import Tenant
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.is_active == True).order_by(Tenant.created_at).limit(1)
        )
        default_tenant = tenant_result.scalar_one_or_none()

        if not default_tenant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="系统未配置默认租户",
            )

        # 创建新用户
        hashed_password = get_password_hash(password)

        # 生成验证令牌
        from app.services.verification import VerificationService
        verification_service = VerificationService(self.db)
        verification_token = verification_service.generate_token()

        db_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_superuser=False,
            tenant_id=default_tenant.id,
            email_verified=False,  # 新用户需要验证邮箱
            verification_token=verification_token,  # 设置验证令牌
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        # 分配默认角色（user角色）
        from app.models.role import Role
        from app.models.user_role import UserRole

        # 查找user角色
        role_result = await self.db.execute(
            select(Role).where(
                Role.name == "user",
                Role.tenant_id == default_tenant.id,
                Role.is_active == True
            )
        )
        user_role = role_result.scalar_one_or_none()

        if user_role:
            # 为用户分配角色
            user_role_assoc = UserRole(
                user_id=db_user.id,
                role_id=user_role.id,
                is_active=True
            )
            self.db.add(user_role_assoc)
            await self.db.commit()

        return db_user

    async def get_user_by_email(self, email: str) -> User | None:
        """通过邮箱获取用户

        Args:
            email: 邮箱地址

        Returns:
            User | None: 用户对象，不存在返回None
        """
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """通过用户名获取用户

        Args:
            username: 用户名

        Returns:
            User | None: 用户对象，不存在返回None
        """
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """验证用户凭据

        Args:
            username: 用户名或邮箱
            password: 密码

        Returns:
            User | None: 验证成功返回用户对象，失败返回None
        """
        from app.core.security import verify_password
        from sqlalchemy import select, or_

        # 通过用户名或邮箱查找用户
        result = await self.db.execute(
            select(User).where(
                or_(User.username == username, User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 验证密码
        if not verify_password(password, user.hashed_password):
            return None

        return user

