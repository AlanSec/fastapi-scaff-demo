from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.bootstrap.container import get_container

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


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
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await container.user_repository.find_by_id(UUID(user_id))
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
    """当前用户的权限集合，格式：resource:action（如 tenant:create）"""
    container = get_container()
    permissions = await container.get_user_permissions_use_case.execute(current_user.id)
    return {f"{p.resource.value}:{p.action.value}" for p in permissions}


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
