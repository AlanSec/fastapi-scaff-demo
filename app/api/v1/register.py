from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.schemas.user import UserRead
from app.services.auth import get_current_user
from app.services.email import email_service
from app.services.user import UserService
from app.services.verification import VerificationService


register_router = APIRouter()
_active = True
_tag = "auth"


async def get_user_service(db: AsyncSession = Depends(get_session)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)


async def get_verification_service(db: AsyncSession = Depends(get_session)) -> VerificationService:
    """获取验证服务实例"""
    return VerificationService(db)


@register_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    user_service: UserService = Depends(get_user_service),
    verification_service: VerificationService = Depends(get_verification_service),
) -> Any:
    """公开用户注册

    注册新用户，系统会自动分配默认tenant和user角色。
    注册后需要验证邮箱才能完全激活账户。
    """
    try:
        # 注册用户
        user = await user_service.register_user(
            email=register_data.email,
            username=register_data.username,
            password=register_data.password
        )

        # 生成验证令牌
        verification_token = await verification_service.create_verification_token(user)

        # 发送验证邮件
        email_sent = await email_service.send_verification_email(
            to_email=user.email,
            verification_token=verification_token,
            username=user.username
        )

        if not email_sent:
            # 如果邮件发送失败，记录日志但继续返回成功（用户可以稍后请求重新发送）
            # 在实际生产环境中，可能需要将邮件加入队列重试
            pass

        # 发送欢迎邮件（可选）
        await email_service.send_welcome_email(
            to_email=user.email,
            username=user.username
        )

        return RegisterResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            message="注册成功，请检查邮箱完成验证"
        )

    except HTTPException:
        # 重新抛出已有的HTTP异常
        raise
    except Exception as e:
        # 捕获其他异常，避免泄露敏感信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误，请稍后重试"
        )


@register_router.get("/register/check-email", response_model=dict)
async def check_email_available(
    email: str,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """检查邮箱是否可用

    用于注册时的实时邮箱可用性检查。
    """
    from sqlalchemy import select
    from app.models.user import User

    result = await user_service.db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    return {
        "email": email,
        "available": existing_user is None
    }


@register_router.get("/register/check-username", response_model=dict)
async def check_username_available(
    username: str,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """检查用户名是否可用

    用于注册时的实时用户名可用性检查。
    """
    from sqlalchemy import select
    from app.models.user import User

    result = await user_service.db.execute(select(User).where(User.username == username))
    existing_user = result.scalar_one_or_none()

    return {
        "username": username,
        "available": existing_user is None
    }


@register_router.get("/register/me", response_model=UserRead)
async def get_current_registered_user(
    current_user=Depends(get_current_user),
) -> Any:
    """获取当前已注册用户信息

    用于注册后获取用户信息（需要登录）。
    """
    return current_user