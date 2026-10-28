"""Password and Verify Routes"""
from fastapi import APIRouter, Depends
from src.api.controllers.password_controller import PasswordController, VerifyController
from src.api.middleware.auth_dependencies import get_current_active_user, rate_limit_by_ip
from src.api.schemas.auth_schema import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from src.bootstrap.container import get_container
from src.domain.entities.user import User


def get_password_controller() -> PasswordController:
    return get_container().password_controller


def get_verify_controller() -> VerifyController:
    return get_container().verify_controller


password_router = APIRouter(prefix="/password", tags=["password"])
verify_router = APIRouter(prefix="/verify", tags=["verify"])

# 邮件类端点防轰炸：单 IP 每小时最多 5 次
_MAIL_IP_LIMIT = 5
_MAIL_IP_WINDOW_SECONDS = 3600


@password_router.post("/forgot", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    _: None = Depends(rate_limit_by_ip("forgot_ip", _MAIL_IP_LIMIT, _MAIL_IP_WINDOW_SECONDS)),
    controller: PasswordController = Depends(get_password_controller)
):
    return await controller.forgot_password(request)


@password_router.post("/reset", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    controller: PasswordController = Depends(get_password_controller)
):
    return await controller.reset_password(request)


@password_router.post("/change", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    controller: PasswordController = Depends(get_password_controller),
):
    """修改密码：身份与租户均来自认证上下文，不接受客户端指定 user_id"""
    return await controller.change_password(request, current_user.id, current_user.tenant_id)


@verify_router.post("/email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    controller: VerifyController = Depends(get_verify_controller)
):
    return await controller.verify_email(request)


@verify_router.post("/resend", response_model=ResendVerificationResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    _: None = Depends(rate_limit_by_ip("resend_ip", _MAIL_IP_LIMIT, _MAIL_IP_WINDOW_SECONDS)),
    controller: VerifyController = Depends(get_verify_controller)
):
    return await controller.resend_verification(request)
