"""Password and Verify Routes"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.api.schemas.auth_schema import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
)
from src.api.controllers.password_controller import PasswordController, VerifyController


_password_controller: Optional[PasswordController] = None
_verify_controller: Optional[VerifyController] = None


def set_password_controller(controller: PasswordController):
    global _password_controller
    _password_controller = controller


def set_verify_controller(controller: VerifyController):
    global _verify_controller
    _verify_controller = controller


def get_password_controller() -> PasswordController:
    if _password_controller is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password controller not initialized"
        )
    return _password_controller


def get_verify_controller() -> VerifyController:
    if _verify_controller is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verify controller not initialized"
        )
    return _verify_controller


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