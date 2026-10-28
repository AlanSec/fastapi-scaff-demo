"""路由注册表——按 API 版本聚合，由 lifespan 循环注册。

新增版本：在对应版本列表中加入 router，或在 API_VERSIONS 中添加新版本键。
"""
from src.api.routes.auth_routes import auth_router
from src.api.routes.password_routes import password_router, verify_router
from src.api.routes.permission_routes import permission_router
from src.api.routes.role_routes import role_router
from src.api.routes.tenant_routes import tenant_router
from src.api.routes.user_admin_routes import user_admin_router

API_VERSIONS: dict[str, list] = {
    "v1": [
        auth_router,
        password_router,
        verify_router,
        tenant_router,
        role_router,
        permission_router,
        user_admin_router,
    ],
}
