from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.db.session import get_session
from app.schemas.auth import VerifyEmailResponse, ResendVerificationRequest, ResendVerificationResponse
from app.services.auth import get_current_user
from app.services.email import email_service
from app.services.verification import VerificationService
from app.models.user import User


verify_router = APIRouter()
_active = True
_tag = "auth"


async def get_verification_service(db: AsyncSession = Depends(get_session)) -> VerificationService:
    """获取验证服务实例"""
    return VerificationService(db)


@verify_router.get("/verify/email", response_model=VerifyEmailResponse)
async def verify_email(
    token: str,
    verification_service: VerificationService = Depends(get_verification_service),
) -> Any:
    """验证邮箱

    使用验证令牌验证用户邮箱。
    """
    user = await verification_service.verify_email_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或过期的验证令牌"
        )

    return VerifyEmailResponse(message="邮箱验证成功")


@verify_router.post("/verify/resend", response_model=ResendVerificationResponse)
async def resend_verification(
    resend_data: ResendVerificationRequest,
    verification_service: VerificationService = Depends(get_verification_service),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """重新发送验证邮件

    为用户重新发送邮箱验证邮件。
    """
    # 查找用户
    result = await db.execute(
        select(User).where(
            User.email == resend_data.email,
            User.is_active == True,
            User.email_verified == False  # 只对未验证的用户重新发送
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        # 出于安全考虑，即使邮箱不存在也返回成功消息
        return ResendVerificationResponse(message="如果该邮箱已注册且未验证，验证邮件将重新发送")

    # 如果用户已有验证令牌，可以重新使用或生成新的
    if not user.verification_token:
        # 生成新的验证令牌
        await verification_service.create_verification_token(user)

    # 发送验证邮件
    email_sent = await email_service.send_verification_email(
        to_email=user.email,
        verification_token=user.verification_token,
        username=user.username
    )

    if email_sent:
        return ResendVerificationResponse(message="验证邮件已重新发送")
    else:
        # 邮件发送失败
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="邮件发送失败，请稍后重试"
        )


@verify_router.get("/verify/status")
async def get_verification_status(
    current_user: User = Depends(get_current_user),  # 需要用户登录
) -> Any:
    """获取验证状态

    获取当前用户的邮箱验证状态（需要登录）。
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录"
        )

    return {
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "needs_verification": not current_user.email_verified
    }


@verify_router.post("/verify/send-test-email")
async def send_test_email(
    email: str,
    current_user: User = Depends(get_current_user),  # 需要用户登录
    db: AsyncSession = Depends(get_session),
) -> Any:
    """发送测试邮件（仅限管理员）

    用于测试邮件服务是否正常工作。
    """
    from app.utils.permissions import PermissionChecker

    # 检查管理员权限
    checker = PermissionChecker(db)
    has_admin = await checker.user_has_role(current_user.id, "admin")
    if not has_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员角色"
        )

    # 发送测试邮件
    test_subject = "测试邮件"
    test_html = """
    <html>
    <body>
        <h2>测试邮件</h2>
        <p>这是一封测试邮件，用于验证邮件服务是否正常工作。</p>
        <p>发送时间: {}</p>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    email_sent = await email_service.send_email(
        to_email=email,
        subject=test_subject,
        html_content=test_html
    )

    if email_sent:
        return {"message": "测试邮件发送成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试邮件发送失败"
        )