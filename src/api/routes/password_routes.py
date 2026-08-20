"""Password and Verify Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends
from src.api.controllers.password_controller import PasswordController, VerifyController
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


def get_password_controller() -> PasswordController:
    return get_container().password_controller


def get_verify_controller() -> VerifyController:
    return get_container().verify_controller


password_router = APIRouter(prefix="/password", tags=["password"])
verify_router = APIRouter(prefix="/verify", tags=["verify"])


@password_router.post("/forgot", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
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
    user_id: UUID,
    controller: PasswordController = Depends(get_password_controller)
):
    return await controller.change_password(request, user_id)


@verify_router.post("/email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    controller: VerifyController = Depends(get_verify_controller)
):
    return await controller.verify_email(request)


@verify_router.post("/resend", response_model=ResendVerificationResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    controller: VerifyController = Depends(get_verify_controller)
):
    return await controller.resend_verification(request)
