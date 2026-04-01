"""Auth Routes - FastAPI router definitions"""
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.schemas.auth_schema import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
_active = True
_tag = "auth"


_controller: "AuthController | None" = None


def set_controller(controller: "AuthController") -> None:
    global _controller
    _controller = controller


def get_controller() -> "AuthController":
    if _controller is None:
        raise RuntimeError("AuthController not initialized")
    return _controller


def _get_controller():
    return get_controller()


@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    controller: "AuthController" = Depends(_get_controller),
):
    try:
        return await controller.register(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    controller: "AuthController" = Depends(_get_controller),
):
    try:
        return await controller.login(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@auth_router.post("/login/json", response_model=TokenResponse)
async def login_json(
    request: LoginRequest,
    controller: "AuthController" = Depends(_get_controller),
):
    try:
        result = await controller.login(request)
        return controller.to_token_response(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))