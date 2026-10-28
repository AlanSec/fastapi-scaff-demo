
from functools import cached_property

from src.api.controllers.auth_controller import AuthController
from src.api.controllers.password_controller import PasswordController, VerifyController
from src.api.controllers.permission_controller import PermissionController
from src.api.controllers.role_controller import RoleController
from src.api.controllers.tenant_controller import TenantController
from src.api.controllers.user_admin_controller import UserAdminController
from src.application.use_cases.association_use_case import (
    AssignPermissionToRoleUseCase,
    AssignRoleToUserUseCase,
    GetRolePermissionsUseCase,
    GetUserPermissionsUseCase,
    GetUserRolesUseCase,
)
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.use_cases.password_use_case import (
    ChangePasswordUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
)
from src.application.use_cases.permission_use_case import (
    CreatePermissionUseCase,
    DeletePermissionUseCase,
    GetPermissionUseCase,
    ListPermissionsUseCase,
    UpdatePermissionUseCase,
)
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.role_use_case import (
    CreateRoleUseCase,
    DeleteRoleUseCase,
    GetRoleUseCase,
    ListRolesUseCase,
    UpdateRoleUseCase,
)
from src.application.use_cases.tenant_use_case import (
    CreateTenantUseCase,
    DeleteTenantUseCase,
    GetTenantUseCase,
    ListTenantsUseCase,
    UpdateTenantUseCase,
)
from src.application.use_cases.user_admin_use_case import (
    AdminCreateUserUseCase,
    AdminDeleteUserUseCase,
    AdminGetCurrentUserUseCase,
    AdminGetUserUseCase,
    AdminListUsersUseCase,
    AdminUpdateCurrentUserUseCase,
    AdminUpdateUserUseCase,
)
from src.application.use_cases.verify_use_case import ResendVerificationUseCase, VerifyEmailUseCase
from src.bootstrap.config import Settings
from src.infrastructure.email.console_email_sender import ConsoleEmailSender
from src.infrastructure.persistence.database import async_session_maker
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_permission_repository import (
    SQLModelPermissionRepository,
)
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_refresh_token_repository import (
    SQLModelRefreshTokenRepository,
)
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_role_repository import SQLModelRoleRepository
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_tenant_repository import SQLModelTenantRepository
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_user_repository import SQLModelUserRepository
from src.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.security.jwt_provider import JWTProviderImpl
from src.infrastructure.security.permission_cache import PermissionCache
from src.infrastructure.security.redis_rate_limiter import RedisRateLimiter


class Container:
    """手动 DI 容器：cached_property 懒加载单例。

    - 每个依赖一个 `@cached_property`，首次访问时构造并缓存
    - 测试注入：`container.user_repository = X`（覆盖缓存）；`reset()` 清空全部缓存
    """

    def __init__(self) -> None:
        pass

    def reset(self) -> None:
        """清空全部懒加载缓存，强制下次访问时重建依赖。

        供测试替换仓储/服务实现使用（替代反射遍历私有属性）。
        """
        for key in [k for k in vars(self) if k != "_initialized"]:
            vars(self).pop(key, None)

    @cached_property
    def config(self) -> Settings:
        return Settings()

    @cached_property
    def password_hasher(self) -> BcryptPasswordHasher:
        return BcryptPasswordHasher()

    @cached_property
    def jwt_provider(self) -> JWTProviderImpl:
        return JWTProviderImpl(
            secret_key=self.config.secret_key,
            algorithm=self.config.algorithm,
            access_token_expire_minutes=self.config.access_token_expire_minutes,
            refresh_token_expire_days=self.config.refresh_token_expire_days,
        )

    @cached_property
    def rate_limiter(self) -> RedisRateLimiter:
        # 生产环境 fail-closed：Redis 不可用时拒绝放行（防打挂 Redis 绕过限流）
        return RedisRateLimiter.from_url(
            self.config.redis_url,
            fail_closed=self.config.environment == "production",
        )

    @cached_property
    def email_sender(self) -> ConsoleEmailSender:
        return ConsoleEmailSender()

    @cached_property
    def permission_cache(self) -> PermissionCache:
        return PermissionCache()

    @cached_property
    def user_repository(self) -> SQLModelUserRepository:
        return SQLModelUserRepository(async_session_maker)

    @cached_property
    def tenant_repository(self) -> SQLModelTenantRepository:
        return SQLModelTenantRepository(async_session_maker)

    @cached_property
    def role_repository(self) -> SQLModelRoleRepository:
        return SQLModelRoleRepository(async_session_maker)

    @cached_property
    def permission_repository(self) -> SQLModelPermissionRepository:
        return SQLModelPermissionRepository(async_session_maker)

    @cached_property
    def refresh_token_repository(self) -> SQLModelRefreshTokenRepository:
        return SQLModelRefreshTokenRepository(async_session_maker)

    # ---- Auth ----

    @cached_property
    def register_use_case(self) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
            tenant_repository=self.tenant_repository,
        )

    @cached_property
    def login_use_case(self) -> LoginUserUseCase:
        return LoginUserUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
            jwt_provider=self.jwt_provider,
            rate_limiter=self.rate_limiter,
            refresh_token_repository=self.refresh_token_repository,
            tenant_repository=self.tenant_repository,
            max_attempts=self.config.max_login_attempts,
            lockout_window_seconds=self.config.login_lockout_minutes * 60,
            require_email_verification=self.config.require_email_verification,
        )

    @cached_property
    def refresh_use_case(self) -> RefreshTokenUseCase:
        return RefreshTokenUseCase(
            user_repository=self.user_repository,
            jwt_provider=self.jwt_provider,
            refresh_token_repository=self.refresh_token_repository,
        )

    @cached_property
    def forgot_password_use_case(self) -> ForgotPasswordUseCase:
        return ForgotPasswordUseCase(
            user_repository=self.user_repository,
            email_sender=self.email_sender,
        )

    @cached_property
    def reset_password_use_case(self) -> ResetPasswordUseCase:
        return ResetPasswordUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
        )

    @cached_property
    def change_password_use_case(self) -> ChangePasswordUseCase:
        return ChangePasswordUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
        )

    @cached_property
    def verify_email_use_case(self) -> VerifyEmailUseCase:
        return VerifyEmailUseCase(user_repository=self.user_repository)

    @cached_property
    def resend_verification_use_case(self) -> ResendVerificationUseCase:
        return ResendVerificationUseCase(
            user_repository=self.user_repository,
            email_sender=self.email_sender,
        )

    @cached_property
    def auth_controller(self) -> AuthController:
        return AuthController(
            register_use_case=self.register_use_case,
            login_use_case=self.login_use_case,
            refresh_use_case=self.refresh_use_case,
        )

    @cached_property
    def password_controller(self) -> PasswordController:
        return PasswordController(
            forgot_password_use_case=self.forgot_password_use_case,
            reset_password_use_case=self.reset_password_use_case,
            change_password_use_case=self.change_password_use_case,
        )

    @cached_property
    def verify_controller(self) -> VerifyController:
        return VerifyController(
            verify_use_case=self.verify_email_use_case,
            resend_use_case=self.resend_verification_use_case,
        )

    # ---- Tenant ----

    @cached_property
    def create_tenant_use_case(self) -> CreateTenantUseCase:
        return CreateTenantUseCase(self.tenant_repository)

    @cached_property
    def get_tenant_use_case(self) -> GetTenantUseCase:
        return GetTenantUseCase(self.tenant_repository)

    @cached_property
    def list_tenants_use_case(self) -> ListTenantsUseCase:
        return ListTenantsUseCase(self.tenant_repository)

    @cached_property
    def update_tenant_use_case(self) -> UpdateTenantUseCase:
        return UpdateTenantUseCase(self.tenant_repository)

    @cached_property
    def delete_tenant_use_case(self) -> DeleteTenantUseCase:
        return DeleteTenantUseCase(self.tenant_repository)

    @cached_property
    def tenant_controller(self) -> TenantController:
        return TenantController(
            create_use_case=self.create_tenant_use_case,
            get_use_case=self.get_tenant_use_case,
            list_use_case=self.list_tenants_use_case,
            update_use_case=self.update_tenant_use_case,
            delete_use_case=self.delete_tenant_use_case,
        )

    # ---- Role ----

    @cached_property
    def create_role_use_case(self) -> CreateRoleUseCase:
        return CreateRoleUseCase(self.role_repository)

    @cached_property
    def get_role_use_case(self) -> GetRoleUseCase:
        return GetRoleUseCase(self.role_repository)

    @cached_property
    def list_roles_use_case(self) -> ListRolesUseCase:
        return ListRolesUseCase(self.role_repository)

    @cached_property
    def update_role_use_case(self) -> UpdateRoleUseCase:
        return UpdateRoleUseCase(self.role_repository)

    @cached_property
    def delete_role_use_case(self) -> DeleteRoleUseCase:
        return DeleteRoleUseCase(self.role_repository)

    # ---- RBAC 关联 ----

    @cached_property
    def assign_role_to_user_use_case(self) -> AssignRoleToUserUseCase:
        return AssignRoleToUserUseCase(
            user_repository=self.user_repository,
            role_repository=self.role_repository,
        )

    @cached_property
    def assign_permission_to_role_use_case(self) -> AssignPermissionToRoleUseCase:
        return AssignPermissionToRoleUseCase(
            role_repository=self.role_repository,
            permission_repository=self.permission_repository,
        )

    @cached_property
    def get_user_roles_use_case(self) -> GetUserRolesUseCase:
        return GetUserRolesUseCase(self.role_repository)

    @cached_property
    def get_role_permissions_use_case(self) -> GetRolePermissionsUseCase:
        return GetRolePermissionsUseCase(
            role_repository=self.role_repository,
            permission_repository=self.permission_repository,
        )

    @cached_property
    def get_user_permissions_use_case(self) -> GetUserPermissionsUseCase:
        return GetUserPermissionsUseCase(
            role_repository=self.role_repository,
            permission_repository=self.permission_repository,
        )

    @cached_property
    def role_controller(self) -> RoleController:
        return RoleController(
            create_use_case=self.create_role_use_case,
            get_use_case=self.get_role_use_case,
            list_use_case=self.list_roles_use_case,
            update_use_case=self.update_role_use_case,
            delete_use_case=self.delete_role_use_case,
            assign_to_user_use_case=self.assign_role_to_user_use_case,
        )

    # ---- Permission ----

    @cached_property
    def create_permission_use_case(self) -> CreatePermissionUseCase:
        return CreatePermissionUseCase(self.permission_repository)

    @cached_property
    def get_permission_use_case(self) -> GetPermissionUseCase:
        return GetPermissionUseCase(self.permission_repository)

    @cached_property
    def list_permissions_use_case(self) -> ListPermissionsUseCase:
        return ListPermissionsUseCase(self.permission_repository)

    @cached_property
    def update_permission_use_case(self) -> UpdatePermissionUseCase:
        return UpdatePermissionUseCase(self.permission_repository)

    @cached_property
    def delete_permission_use_case(self) -> DeletePermissionUseCase:
        return DeletePermissionUseCase(self.permission_repository)

    @cached_property
    def permission_controller(self) -> PermissionController:
        return PermissionController(
            create_use_case=self.create_permission_use_case,
            get_use_case=self.get_permission_use_case,
            list_use_case=self.list_permissions_use_case,
            update_use_case=self.update_permission_use_case,
            delete_use_case=self.delete_permission_use_case,
            assign_to_role_use_case=self.assign_permission_to_role_use_case,
        )

    # ---- User Admin ----

    @cached_property
    def admin_create_user_use_case(self) -> AdminCreateUserUseCase:
        return AdminCreateUserUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
        )

    @cached_property
    def admin_list_users_use_case(self) -> AdminListUsersUseCase:
        return AdminListUsersUseCase(self.user_repository)

    @cached_property
    def admin_get_user_use_case(self) -> AdminGetUserUseCase:
        return AdminGetUserUseCase(self.user_repository)

    @cached_property
    def admin_update_user_use_case(self) -> AdminUpdateUserUseCase:
        return AdminUpdateUserUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
        )

    @cached_property
    def admin_delete_user_use_case(self) -> AdminDeleteUserUseCase:
        return AdminDeleteUserUseCase(self.user_repository)

    @cached_property
    def admin_get_current_user_use_case(self) -> AdminGetCurrentUserUseCase:
        return AdminGetCurrentUserUseCase(self.user_repository)

    @cached_property
    def admin_update_current_user_use_case(self) -> AdminUpdateCurrentUserUseCase:
        return AdminUpdateCurrentUserUseCase(self.user_repository)

    @cached_property
    def user_admin_controller(self) -> UserAdminController:
        return UserAdminController(
            create_use_case=self.admin_create_user_use_case,
            list_use_case=self.admin_list_users_use_case,
            get_use_case=self.admin_get_user_use_case,
            update_use_case=self.admin_update_user_use_case,
            delete_use_case=self.admin_delete_user_use_case,
            get_current_use_case=self.admin_get_current_user_use_case,
            update_current_use_case=self.admin_update_current_user_use_case,
        )


_container_instance: Container | None = None


def get_container() -> Container:
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance
