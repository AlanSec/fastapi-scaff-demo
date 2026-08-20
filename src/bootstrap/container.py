
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
from src.infrastructure.security.redis_rate_limiter import RedisRateLimiter


class Container:
    _instance = None

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._config = None
        self._password_hasher = None
        self._jwt_provider = None
        self._rate_limiter = None
        self._email_sender = None
        self._user_repository = None
        self._refresh_token_repository = None
        self._register_use_case = None
        self._login_use_case = None
        self._refresh_use_case = None
        self._forgot_password_use_case = None
        self._reset_password_use_case = None
        self._change_password_use_case = None
        self._verify_email_use_case = None
        self._resend_verification_use_case = None
        self._auth_controller = None
        self._password_controller = None
        self._verify_controller = None
        self._tenant_repository = None
        self._role_repository = None
        self._permission_repository = None
        self._assign_role_to_user_use_case = None
        self._assign_permission_to_role_use_case = None
        self._get_user_roles_use_case = None
        self._get_role_permissions_use_case = None
        self._get_user_permissions_use_case = None
        self._create_tenant_use_case = None
        self._get_tenant_use_case = None
        self._list_tenants_use_case = None
        self._update_tenant_use_case = None
        self._delete_tenant_use_case = None
        self._create_role_use_case = None
        self._get_role_use_case = None
        self._list_roles_use_case = None
        self._update_role_use_case = None
        self._delete_role_use_case = None
        self._create_permission_use_case = None
        self._get_permission_use_case = None
        self._list_permissions_use_case = None
        self._update_permission_use_case = None
        self._delete_permission_use_case = None
        self._tenant_controller = None
        self._role_controller = None
        self._permission_controller = None
        self._admin_create_user_use_case = None
        self._admin_list_users_use_case = None
        self._admin_get_user_use_case = None
        self._admin_update_user_use_case = None
        self._admin_delete_user_use_case = None
        self._admin_get_current_user_use_case = None
        self._admin_update_current_user_use_case = None
        self._user_admin_controller = None

    @property
    def config(self) -> Settings:
        if self._config is None:
            self._config = Settings()
        return self._config

    @property
    def password_hasher(self) -> BcryptPasswordHasher:
        if self._password_hasher is None:
            self._password_hasher = BcryptPasswordHasher()
        return self._password_hasher

    @property
    def jwt_provider(self) -> JWTProviderImpl:
        if self._jwt_provider is None:
            self._jwt_provider = JWTProviderImpl(
                secret_key=self.config.secret_key,
                algorithm=self.config.algorithm,
                access_token_expire_minutes=self.config.access_token_expire_minutes,
                refresh_token_expire_days=self.config.refresh_token_expire_days,
            )
        return self._jwt_provider

    @property
    def rate_limiter(self) -> RedisRateLimiter:
        if self._rate_limiter is None:
            self._rate_limiter = RedisRateLimiter.from_url(self.config.redis_url)
        return self._rate_limiter

    @property
    def email_sender(self) -> ConsoleEmailSender:
        if self._email_sender is None:
            self._email_sender = ConsoleEmailSender()
        return self._email_sender

    @property
    def user_repository(self) -> SQLModelUserRepository:
        if self._user_repository is None:
            self._user_repository = SQLModelUserRepository(async_session_maker)
        return self._user_repository

    @property
    def tenant_repository(self) -> SQLModelTenantRepository:
        if self._tenant_repository is None:
            self._tenant_repository = SQLModelTenantRepository(async_session_maker)
        return self._tenant_repository

    @property
    def role_repository(self) -> SQLModelRoleRepository:
        if self._role_repository is None:
            self._role_repository = SQLModelRoleRepository(async_session_maker)
        return self._role_repository

    @property
    def permission_repository(self) -> SQLModelPermissionRepository:
        if self._permission_repository is None:
            self._permission_repository = SQLModelPermissionRepository(async_session_maker)
        return self._permission_repository

    @property
    def refresh_token_repository(self) -> SQLModelRefreshTokenRepository:
        if self._refresh_token_repository is None:
            self._refresh_token_repository = SQLModelRefreshTokenRepository(async_session_maker)
        return self._refresh_token_repository

    @property
    def register_use_case(self) -> RegisterUserUseCase:
        if self._register_use_case is None:
            self._register_use_case = RegisterUserUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
                tenant_repository=self.tenant_repository,
            )
        return self._register_use_case

    @property
    def login_use_case(self) -> LoginUserUseCase:
        if self._login_use_case is None:
            self._login_use_case = LoginUserUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
                jwt_provider=self.jwt_provider,
                rate_limiter=self.rate_limiter,
                refresh_token_repository=self.refresh_token_repository,
                max_attempts=self.config.max_login_attempts,
                lockout_window_seconds=self.config.login_lockout_minutes * 60,
                require_email_verification=self.config.require_email_verification,
            )
        return self._login_use_case

    @property
    def refresh_use_case(self) -> RefreshTokenUseCase:
        if self._refresh_use_case is None:
            self._refresh_use_case = RefreshTokenUseCase(
                user_repository=self.user_repository,
                jwt_provider=self.jwt_provider,
                refresh_token_repository=self.refresh_token_repository,
            )
        return self._refresh_use_case

    @property
    def forgot_password_use_case(self) -> ForgotPasswordUseCase:
        if self._forgot_password_use_case is None:
            self._forgot_password_use_case = ForgotPasswordUseCase(
                user_repository=self.user_repository,
                email_sender=self.email_sender,
            )
        return self._forgot_password_use_case

    @property
    def reset_password_use_case(self) -> ResetPasswordUseCase:
        if self._reset_password_use_case is None:
            self._reset_password_use_case = ResetPasswordUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
            )
        return self._reset_password_use_case

    @property
    def change_password_use_case(self) -> ChangePasswordUseCase:
        if self._change_password_use_case is None:
            self._change_password_use_case = ChangePasswordUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
            )
        return self._change_password_use_case

    @property
    def verify_email_use_case(self) -> VerifyEmailUseCase:
        if self._verify_email_use_case is None:
            self._verify_email_use_case = VerifyEmailUseCase(
                user_repository=self.user_repository,
            )
        return self._verify_email_use_case

    @property
    def resend_verification_use_case(self) -> ResendVerificationUseCase:
        if self._resend_verification_use_case is None:
            self._resend_verification_use_case = ResendVerificationUseCase(
                user_repository=self.user_repository,
                email_sender=self.email_sender,
            )
        return self._resend_verification_use_case

    @property
    def auth_controller(self) -> AuthController:
        if self._auth_controller is None:
            self._auth_controller = AuthController(
                register_use_case=self.register_use_case,
                login_use_case=self.login_use_case,
                refresh_use_case=self.refresh_use_case,
            )
        return self._auth_controller

    @property
    def password_controller(self) -> PasswordController:
        if self._password_controller is None:
            self._password_controller = PasswordController(
                forgot_password_use_case=self.forgot_password_use_case,
                reset_password_use_case=self.reset_password_use_case,
                change_password_use_case=self.change_password_use_case,
            )
        return self._password_controller

    @property
    def verify_controller(self) -> VerifyController:
        if self._verify_controller is None:
            self._verify_controller = VerifyController(
                verify_use_case=self.verify_email_use_case,
                resend_use_case=self.resend_verification_use_case,
            )
        return self._verify_controller

    # ---- Tenant ----

    @property
    def create_tenant_use_case(self) -> CreateTenantUseCase:
        if self._create_tenant_use_case is None:
            self._create_tenant_use_case = CreateTenantUseCase(self.tenant_repository)
        return self._create_tenant_use_case

    @property
    def get_tenant_use_case(self) -> GetTenantUseCase:
        if self._get_tenant_use_case is None:
            self._get_tenant_use_case = GetTenantUseCase(self.tenant_repository)
        return self._get_tenant_use_case

    @property
    def list_tenants_use_case(self) -> ListTenantsUseCase:
        if self._list_tenants_use_case is None:
            self._list_tenants_use_case = ListTenantsUseCase(self.tenant_repository)
        return self._list_tenants_use_case

    @property
    def update_tenant_use_case(self) -> UpdateTenantUseCase:
        if self._update_tenant_use_case is None:
            self._update_tenant_use_case = UpdateTenantUseCase(self.tenant_repository)
        return self._update_tenant_use_case

    @property
    def delete_tenant_use_case(self) -> DeleteTenantUseCase:
        if self._delete_tenant_use_case is None:
            self._delete_tenant_use_case = DeleteTenantUseCase(self.tenant_repository)
        return self._delete_tenant_use_case

    @property
    def tenant_controller(self) -> TenantController:
        if self._tenant_controller is None:
            self._tenant_controller = TenantController(
                create_use_case=self.create_tenant_use_case,
                get_use_case=self.get_tenant_use_case,
                list_use_case=self.list_tenants_use_case,
                update_use_case=self.update_tenant_use_case,
                delete_use_case=self.delete_tenant_use_case,
            )
        return self._tenant_controller

    # ---- Role ----

    @property
    def create_role_use_case(self) -> CreateRoleUseCase:
        if self._create_role_use_case is None:
            self._create_role_use_case = CreateRoleUseCase(self.role_repository)
        return self._create_role_use_case

    @property
    def get_role_use_case(self) -> GetRoleUseCase:
        if self._get_role_use_case is None:
            self._get_role_use_case = GetRoleUseCase(self.role_repository)
        return self._get_role_use_case

    @property
    def list_roles_use_case(self) -> ListRolesUseCase:
        if self._list_roles_use_case is None:
            self._list_roles_use_case = ListRolesUseCase(self.role_repository)
        return self._list_roles_use_case

    @property
    def update_role_use_case(self) -> UpdateRoleUseCase:
        if self._update_role_use_case is None:
            self._update_role_use_case = UpdateRoleUseCase(self.role_repository)
        return self._update_role_use_case

    @property
    def delete_role_use_case(self) -> DeleteRoleUseCase:
        if self._delete_role_use_case is None:
            self._delete_role_use_case = DeleteRoleUseCase(self.role_repository)
        return self._delete_role_use_case

    # ---- RBAC 关联 ----

    @property
    def assign_role_to_user_use_case(self) -> AssignRoleToUserUseCase:
        if self._assign_role_to_user_use_case is None:
            self._assign_role_to_user_use_case = AssignRoleToUserUseCase(
                user_repository=self.user_repository,
                role_repository=self.role_repository,
            )
        return self._assign_role_to_user_use_case

    @property
    def assign_permission_to_role_use_case(self) -> AssignPermissionToRoleUseCase:
        if self._assign_permission_to_role_use_case is None:
            self._assign_permission_to_role_use_case = AssignPermissionToRoleUseCase(
                role_repository=self.role_repository,
                permission_repository=self.permission_repository,
            )
        return self._assign_permission_to_role_use_case

    @property
    def get_user_roles_use_case(self) -> GetUserRolesUseCase:
        if self._get_user_roles_use_case is None:
            self._get_user_roles_use_case = GetUserRolesUseCase(self.role_repository)
        return self._get_user_roles_use_case

    @property
    def get_role_permissions_use_case(self) -> GetRolePermissionsUseCase:
        if self._get_role_permissions_use_case is None:
            self._get_role_permissions_use_case = GetRolePermissionsUseCase(self.permission_repository)
        return self._get_role_permissions_use_case

    @property
    def get_user_permissions_use_case(self) -> GetUserPermissionsUseCase:
        if self._get_user_permissions_use_case is None:
            self._get_user_permissions_use_case = GetUserPermissionsUseCase(
                role_repository=self.role_repository,
                permission_repository=self.permission_repository,
            )
        return self._get_user_permissions_use_case

    @property
    def role_controller(self) -> RoleController:
        if self._role_controller is None:
            self._role_controller = RoleController(
                create_use_case=self.create_role_use_case,
                get_use_case=self.get_role_use_case,
                list_use_case=self.list_roles_use_case,
                update_use_case=self.update_role_use_case,
                delete_use_case=self.delete_role_use_case,
                assign_to_user_use_case=self.assign_role_to_user_use_case,
            )
        return self._role_controller

    # ---- Permission ----

    @property
    def create_permission_use_case(self) -> CreatePermissionUseCase:
        if self._create_permission_use_case is None:
            self._create_permission_use_case = CreatePermissionUseCase(self.permission_repository)
        return self._create_permission_use_case

    @property
    def get_permission_use_case(self) -> GetPermissionUseCase:
        if self._get_permission_use_case is None:
            self._get_permission_use_case = GetPermissionUseCase(self.permission_repository)
        return self._get_permission_use_case

    @property
    def list_permissions_use_case(self) -> ListPermissionsUseCase:
        if self._list_permissions_use_case is None:
            self._list_permissions_use_case = ListPermissionsUseCase(self.permission_repository)
        return self._list_permissions_use_case

    @property
    def update_permission_use_case(self) -> UpdatePermissionUseCase:
        if self._update_permission_use_case is None:
            self._update_permission_use_case = UpdatePermissionUseCase(self.permission_repository)
        return self._update_permission_use_case

    @property
    def delete_permission_use_case(self) -> DeletePermissionUseCase:
        if self._delete_permission_use_case is None:
            self._delete_permission_use_case = DeletePermissionUseCase(self.permission_repository)
        return self._delete_permission_use_case

    @property
    def permission_controller(self) -> PermissionController:
        if self._permission_controller is None:
            self._permission_controller = PermissionController(
                create_use_case=self.create_permission_use_case,
                get_use_case=self.get_permission_use_case,
                list_use_case=self.list_permissions_use_case,
                update_use_case=self.update_permission_use_case,
                delete_use_case=self.delete_permission_use_case,
                assign_to_role_use_case=self.assign_permission_to_role_use_case,
            )
        return self._permission_controller

    # ---- User Admin ----

    @property
    def admin_create_user_use_case(self) -> AdminCreateUserUseCase:
        if self._admin_create_user_use_case is None:
            self._admin_create_user_use_case = AdminCreateUserUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
            )
        return self._admin_create_user_use_case

    @property
    def admin_list_users_use_case(self) -> AdminListUsersUseCase:
        if self._admin_list_users_use_case is None:
            self._admin_list_users_use_case = AdminListUsersUseCase(self.user_repository)
        return self._admin_list_users_use_case

    @property
    def admin_get_user_use_case(self) -> AdminGetUserUseCase:
        if self._admin_get_user_use_case is None:
            self._admin_get_user_use_case = AdminGetUserUseCase(self.user_repository)
        return self._admin_get_user_use_case

    @property
    def admin_update_user_use_case(self) -> AdminUpdateUserUseCase:
        if self._admin_update_user_use_case is None:
            self._admin_update_user_use_case = AdminUpdateUserUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
            )
        return self._admin_update_user_use_case

    @property
    def admin_delete_user_use_case(self) -> AdminDeleteUserUseCase:
        if self._admin_delete_user_use_case is None:
            self._admin_delete_user_use_case = AdminDeleteUserUseCase(self.user_repository)
        return self._admin_delete_user_use_case

    @property
    def admin_get_current_user_use_case(self) -> AdminGetCurrentUserUseCase:
        if self._admin_get_current_user_use_case is None:
            self._admin_get_current_user_use_case = AdminGetCurrentUserUseCase(self.user_repository)
        return self._admin_get_current_user_use_case

    @property
    def admin_update_current_user_use_case(self) -> AdminUpdateCurrentUserUseCase:
        if self._admin_update_current_user_use_case is None:
            self._admin_update_current_user_use_case = AdminUpdateCurrentUserUseCase(self.user_repository)
        return self._admin_update_current_user_use_case

    @property
    def user_admin_controller(self) -> UserAdminController:
        if self._user_admin_controller is None:
            self._user_admin_controller = UserAdminController(
                create_use_case=self.admin_create_user_use_case,
                list_use_case=self.admin_list_users_use_case,
                get_use_case=self.admin_get_user_use_case,
                update_use_case=self.admin_update_user_use_case,
                delete_use_case=self.admin_delete_user_use_case,
                get_current_use_case=self.admin_get_current_user_use_case,
                update_current_use_case=self.admin_update_current_user_use_case,
            )
        return self._user_admin_controller


_container_instance: Container | None = None


def get_container() -> Container:
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance
