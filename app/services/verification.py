import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User


class VerificationService:
    """验证服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_token(self, length: int = 32) -> str:
        """生成安全的随机令牌

        Args:
            length: 令牌长度

        Returns:
            str: 随机令牌
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def get_token_expiry(self, hours: int = 24) -> datetime:
        """获取令牌过期时间

        Args:
            hours: 有效小时数

        Returns:
            datetime: 过期时间
        """
        return datetime.now() + timedelta(hours=hours)

    def is_token_expired(self, expiry_time: Optional[datetime]) -> bool:
        """检查令牌是否过期

        Args:
            expiry_time: 过期时间

        Returns:
            bool: 是否已过期
        """
        if expiry_time is None:
            return True
        return datetime.now() > expiry_time

    async def create_verification_token(self, user: User) -> str:
        """为用户创建邮箱验证令牌

        Args:
            user: 用户对象

        Returns:
            str: 验证令牌
        """
        token = self.generate_token()
        expiry = self.get_token_expiry(hours=24)  # 24小时有效

        user.verification_token = token
        # 注意：reset_token_expires字段用于重置令牌过期时间，这里我们暂时不存储验证令牌过期时间
        # 或者可以复用reset_token_expires字段，但为了清晰，我们暂时不存储验证令牌过期时间
        # 验证令牌通常通过创建时间判断过期，这里简化处理

        await self.db.commit()
        await self.db.refresh(user)

        return token

    async def verify_email_token(self, token: str) -> Optional[User]:
        """验证邮箱验证令牌

        Args:
            token: 验证令牌

        Returns:
            Optional[User]: 验证成功返回用户对象，失败返回None
        """
        result = await self.db.execute(
            select(User).where(
                User.verification_token == token,
                User.is_active == True
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 验证成功，更新用户状态
        user.email_verified = True
        user.verification_token = None  # 清除令牌，防止重用
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def create_password_reset_token(self, user: User) -> str:
        """为用户创建密码重置令牌

        Args:
            user: 用户对象

        Returns:
            str: 重置令牌
        """
        token = self.generate_token()
        expiry = self.get_token_expiry(hours=1)  # 1小时有效

        user.reset_token = token
        user.reset_token_expires = expiry

        await self.db.commit()
        await self.db.refresh(user)

        return token

    async def verify_password_reset_token(self, token: str) -> Optional[User]:
        """验证密码重置令牌

        Args:
            token: 重置令牌

        Returns:
            Optional[User]: 验证成功返回用户对象，失败返回None
        """
        result = await self.db.execute(
            select(User).where(
                User.reset_token == token,
                User.is_active == True
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 检查令牌是否过期
        if self.is_token_expired(user.reset_token_expires):
            # 清除过期令牌
            user.reset_token = None
            user.reset_token_expires = None
            await self.db.commit()
            return None

        return user

    async def clear_password_reset_token(self, user: User) -> None:
        """清除用户的密码重置令牌

        Args:
            user: 用户对象
        """
        user.reset_token = None
        user.reset_token_expires = None
        await self.db.commit()
        await self.db.refresh(user)

    async def clear_verification_token(self, user: User) -> None:
        """清除用户的邮箱验证令牌

        Args:
            user: 用户对象
        """
        user.verification_token = None
        await self.db.commit()
        await self.db.refresh(user)