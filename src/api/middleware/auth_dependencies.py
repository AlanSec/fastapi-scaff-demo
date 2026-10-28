from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from src.bootstrap.container import get_container

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def rate_limit_by_ip(prefix: str, limit: int, window_seconds: int):
    """按客户端 IP 限流的通用依赖（注册/忘记密码/重发验证等防滥用端点）。

    与登录限流（失败计数）不同，这里对端点总调用次数计数。
    """

    async def checker(request: Request):
        container = get_container()
        client_ip = request.client.host if request.client else "unknown"
        allowed = await container.rate_limiter.check_rate_limit(
            f"{prefix}:{client_ip}", limit, window_seconds
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please try again later",
            )

    return checker


async def get_current_user(token: str = Depends(oauth2_scheme)):
    container = get_container()
    payload = container.jwt_provider.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 只接受 access token——refresh token 不能当 access token 使用
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if user_id is None or tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # 租户一致性：按 (user_id, tenant_id) 查询——令牌内租户与用户实际租户
    # 不一致（或旧令牌缺 claim）时查不到用户，直接 401
    user = await container.user_repository.find_by_id(UUID(user_id), UUID(tenant_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_active_superuser(
    current_user = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a superuser",
        )
    return current_user


async def get_current_user_permissions(
    current_user = Depends(get_current_active_user),
) -> set[str]:
    """当前用户的权限集合，格式：resource:action（如 tenant:create）。

    - superuser 短路：不查库（require_permissions 对 superuser 直接放行）
    - 普通用户走内存 TTL 缓存：权限查询从每请求 4~5 次 DB 往返降为 1 次
    - 角色/权限分配后由路由层主动失效（见 role_routes / permission_routes）
    """
    if current_user.is_superuser:
        return set()

    container = get_container()
    cache_key = str(current_user.id)
    cached = container.permission_cache.get(cache_key)
    if cached is not None:
        return cached

    permissions = await container.get_user_permissions_use_case.execute(
        current_user.id, current_user.tenant_id
    )
    result = {f"{p.resource.value}:{p.action.value}" for p in permissions}
    container.permission_cache.set(cache_key, result)
    return result


def require_permissions(*required: str):
    """权限校验依赖：superuser 直接放行，否则要求具备全部指定权限"""
    async def checker(
        current_user = Depends(get_current_active_user),
        permissions: set[str] = Depends(get_current_user_permissions),
    ):
        if current_user.is_superuser:
            return current_user
        missing = [p for p in required if p not in permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return current_user
    return checker
