from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.db.session import get_session
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth import get_current_user
from app.services.email import email_service
from app.services.verification import VerificationService
from app.models.user import User


password_router = APIRouter()
_active = True
_tag = "auth"


async def get_verification_service(db: AsyncSession = Depends(get_session)) -> VerificationService:
    """获取验证服务实例"""
    return VerificationService(db)


@password_router.post("/password/forgot")
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """忘记密码请求

    发送密码重置链接到用户邮箱。
    """
    # 查找用户
    result = await db.execute(
        select(User).where(
            User.email == forgot_data.email,
            User.is_active == True
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        # 出于安全考虑，即使邮箱不存在也返回成功消息
        return {"message": "如果该邮箱已注册，重置链接将发送到您的邮箱"}

    # 生成密码重置令牌
    reset_token = await verification_service.create_password_reset_token(user)

    # 发送重置邮件
    email_sent = await email_service.send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        username=user.username
    )

    if email_sent:
        return {"message": "重置链接已发送到您的邮箱"}
    else:
        # 邮件发送失败
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="邮件发送失败，请稍后重试"
        )


@password_router.post("/password/reset")
async def reset_password(
    reset_data: ResetPasswordRequest,
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """重置密码

    使用重置令牌设置新密码。
    """
    # 验证重置令牌
    user = await verification_service.verify_password_reset_token(reset_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或过期的重置令牌"
        )

    # 更新密码
    user.hashed_password = get_password_hash(reset_data.new_password)

    # 清除重置令牌
    await verification_service.clear_password_reset_token(user)

    await db.commit()
    await db.refresh(user)

    return {"message": "密码重置成功"}


@password_router.post("/password/change")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),  # 需要用户登录
    db: AsyncSession = Depends(get_session),
) -> Any:
    """更改密码（需要登录）

    登录用户更改自己的密码。
    """
    from app.core.security import verify_password

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录"
        )

    # 验证当前密码
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确"
        )

    # 更新密码
    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()

    return {"message": "密码更改成功"}