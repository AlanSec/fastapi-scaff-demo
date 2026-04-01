from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.db.session import get_session
from app.schemas.auth import ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth import get_current_user
from app.services.email import email_service
from app.services.verification import VerificationService
from app.models.user import User
from app.api.rate_limit import rate_limit


password_router = APIRouter()
_active = True
_tag = "auth"


async def get_verification_service(db: AsyncSession = Depends(get_session)) -> VerificationService:
    """获取验证服务实例"""
    return VerificationService(db)


@password_router.post("/password/forgot")
@rate_limit(max_requests=3, window_seconds=60)
async def forgot_password(
    request: Request,
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
@rate_limit(max_requests=5, window_seconds=60)
async def reset_password(
    request: Request,
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
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """更改密码（需要登录）"""
    from app.core.security import verify_password

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录"
        )

    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "密码更改成功"}