"""Auth Routes - FastAPI router definitions"""
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from src.api.controllers.auth_controller import AuthController
from src.api.middleware.auth_dependencies import rate_limit_by_ip
from src.api.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    OAuth2TokenResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from src.bootstrap.container import get_container
from src.domain.exceptions import InvalidCredentialsError

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# 开放注册防滥用：单 IP 每小时最多 10 次注册
_REGISTER_IP_LIMIT = 10
_REGISTER_IP_WINDOW_SECONDS = 3600


def _get_controller() -> "AuthController":
    """从 DI 容器获取 AuthController（路由不再持有模块级可变全局）"""
    return get_container().auth_controller


async def _record_failed_login_from_ip(request: Request) -> None:
    """登录失败时按客户端 IP 计数，防止跨账号暴力破解"""
    container = get_container()
    client_ip = request.client.host if request.client else "unknown"
    key = f"login_ip:{client_ip}"
    allowed = await container.rate_limiter.check_rate_limit(
        key,
        container.config.max_login_attempts,
        container.config.login_lockout_minutes * 60,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, please try again later",
        )


@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    _: None = Depends(rate_limit_by_ip("register_ip", _REGISTER_IP_LIMIT, _REGISTER_IP_WINDOW_SECONDS)),
    controller: "AuthController" = Depends(_get_controller),
):
    # 业务错误（邮箱冲突 409 / 输入无效 400）由全局领域异常 handler 映射
    return await controller.register(request)


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    controller: "AuthController" = Depends(_get_controller),
):
    try:
        return await controller.login(request)
    except InvalidCredentialsError:
        # 失败尝试按 IP 计数（防跨账号爆破）；状态码由全局 handler 映射 401
        await _record_failed_login_from_ip(http_request)
        raise


@auth_router.post("/login/json", response_model=TokenResponse)
async def login_json(
    request: LoginRequest,
    http_request: Request,
    controller: "AuthController" = Depends(_get_controller),
):
    try:
        result = await controller.login(request)
        return controller.to_token_response(result)
    except InvalidCredentialsError:
        await _record_failed_login_from_ip(http_request)
        raise


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    controller: "AuthController" = Depends(_get_controller),
):
    return await controller.refresh(request)


async def _default_tenant_id() -> Optional[str]:
    """token 表单未指定租户时回退到默认租户"""
    container = get_container()
    tenant = await container.tenant_repository.find_by_name("Default Tenant")
    if tenant is not None:
        return str(tenant.id)
    tenants = await container.tenant_repository.find_all(limit=1)
    return str(tenants[0].id) if tenants else None


@auth_router.post("/token", response_model=OAuth2TokenResponse)
async def oauth2_token(
    http_request: Request,
    username: str = Form(...),
    password: str = Form(...),
    tenant_id: Optional[str] = Form(None),
    controller: "AuthController" = Depends(_get_controller),
):
    """OAuth2 密码模式令牌端点（修复 Swagger Authorize）"""
    resolved_tenant_id = tenant_id or await _default_tenant_id()
    if resolved_tenant_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No tenant available")

    try:
        result = await controller.login(
            LoginRequest(email=username, password=password, tenant_id=resolved_tenant_id)
        )
        return OAuth2TokenResponse(access_token=result.access_token)
    except InvalidCredentialsError:
        await _record_failed_login_from_ip(http_request)
        raise
