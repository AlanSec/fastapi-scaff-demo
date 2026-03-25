from datetime import datetime, timedelta
from uuid import UUID, uuid4
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_session
from app.models.user import User
from app.models.refresh_token import RefreshToken


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")


async def authenticate_user(username_or_email: str, password: str, db: AsyncSession) -> User | None:
    """验证用户凭据

    Args:
        username_or_email: 用户名或邮箱
        password: 用户密码
        db: 数据库会话

    Returns:
        Optional[User]: 验证成功返回用户对象，失败返回None
    """
    result = await db.execute(
        select(User).where(or_(User.email == username_or_email, User.username == username_or_email))
    )
    user = result.scalar_one_or_none()

    if not user:
        return None

    # 检查账户是否被锁定
    if user.locked_until and user.locked_until > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"账户已被锁定，请在 {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')} 后重试"
        )

    # 验证密码
    if not verify_password(password, user.hashed_password):
        # 增加失败计数
        user.failed_login_attempts += 1

        # 检查是否需要锁定账户
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"登录失败次数过多，账户已被锁定 {settings.LOGIN_LOCKOUT_MINUTES} 分钟"
            )

        await db.commit()
        return None

    # 登录成功，重置失败计数
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()

    return user


def generate_refresh_token() -> str:
    """生成安全的刷新令牌

    Returns:
        str: 随机刷新令牌
    """
    return secrets.token_urlsafe(64)


async def create_user_token(user_id: UUID, db: AsyncSession) -> dict:
    """为用户创建访问令牌和刷新令牌

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        dict: 包含访问令牌、刷新令牌和令牌类型的字典
    """
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=str(user_id), expires_delta=access_token_expires)

    # 创建刷新令牌
    refresh_token_value = generate_refresh_token()
    refresh_token_expires = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        id=uuid4(),
        user_id=user_id,
        token=refresh_token_value,
        expires_at=refresh_token_expires,
        is_revoked=False
    )
    db.add(refresh_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "Bearer"
    }


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    """使用刷新令牌获取新的访问令牌

    Args:
        refresh_token: 刷新令牌
        db: 数据库会话

    Returns:
        dict: 包含新访问令牌、新刷新令牌和令牌类型的字典

    Raises:
        HTTPException: 刷新令牌无效或已过期时抛出
    """
    # 查找刷新令牌
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    # 检查令牌是否过期
    if token_record.expires_at < datetime.now():
        await db.delete(token_record)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已过期"
        )

    # 撤销旧的刷新令牌（令牌轮换）
    token_record.is_revoked = True
    await db.commit()

    # 创建新的访问令牌和刷新令牌
    return await create_user_token(token_record.user_id, db)


import logging

logger = logging.getLogger(__name__)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    logger.info(f"收到 token: [{token}]")
    logger.info(f"Token 长度: {len(token) if token else 0}")
    logger.info(f"Token 部分数: {len(token.split('.')) if token else 0}")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        logger.info(f"Token 解码成功, user_id: {user_id}")
        if user_id is None:
            logger.warning("Token 中 sub 字段为空")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"Token 解码失败: {e}")
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning(f"用户不存在: {user_id}")
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级管理员用户

    Args:
        current_user: 当前用户

    Returns:
        User: 当前超级管理员用户

    Raises:
        HTTPException: 用户不是超级管理员时抛出
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户权限不足",
        )
    return current_user
