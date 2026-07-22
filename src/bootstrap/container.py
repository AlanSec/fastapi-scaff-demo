from dataclasses import dataclass

from src.bootstrap.config import Settings
from src.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.security.jwt_provider import JWTProviderImpl
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.persistence.in_memory.in_memory_tenant_repository import InMemoryTenantRepository
from src.infrastructure.persistence.in_memory.in_memory_role_repository import InMemoryRoleRepository
from src.infrastructure.persistence.in_memory.in_memory_permission_repository import InMemoryPermissionRepository
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.use_cases.password_use_case import (
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
    ChangePasswordUseCase,
)
from src.application.use_cases.verify_use_case import VerifyEmailUseCase, ResendVerificationUseCase
from src.application.use_cases.tenant_use_case import (
    CreateTenantUseCase, GetTenantUseCase, ListTenantsUseCase,
    UpdateTenantUseCase, DeleteTenantUseCase,
)
from src.application.use_cases.role_use_case import (
    CreateRoleUseCase, GetRoleUseCase, ListRolesUseCase,
    UpdateRoleUseCase, DeleteRoleUseCase,
)
from src.application.use_cases.permission_use_case import (
    CreatePermissionUseCase, GetPermissionUseCase, ListPermissionsUseCase,
    UpdatePermissionUseCase, DeletePermissionUseCase,
)
from src.api.controllers.auth_controller import AuthController
from src.api.controllers.tenant_controller import TenantController
from src.api.controllers.role_controller import RoleController
from src.api.controllers.permission_controller import PermissionController
from src.application.use_cases.user_admin_use_case import (
    AdminCreateUserUseCase, AdminListUsersUseCase, AdminGetUserUseCase,
    AdminUpdateUserUseCase, AdminDeleteUserUseCase,
    AdminGetCurrentUserUseCase, AdminUpdateCurrentUserUseCase,
)
from src.api.controllers.user_admin_controller import UserAdminController
from src.api.controllers.password_controller import PasswordController, VerifyController


class Container:
    _instance = None

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._config = None
        self._password_hasher = None
        self._jwt_provider = None
        self._user_repository = None
        self._register_use_case = None
        self._login_use_case = None
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
    def user_repository(self) -> InMemoryUserRepository:
        if self._user_repository is None:
            self._user_repository = InMemoryUserRepository()
        return self._user_repository

    @property
    def tenant_repository(self) -> InMemoryTenantRepository:
        if self._tenant_repository is None:
            self._tenant_repository = InMemoryTenantRepository()
        return self._tenant_repository

    @property
    def role_repository(self) -> InMemoryRoleRepository:
        if self._role_repository is None:
            self._role_repository = InMemoryRoleRepository()
        return self._role_repository

    @property
    def permission_repository(self) -> InMemoryPermissionRepository:
        if self._permission_repository is None:
            self._permission_repository = InMemoryPermissionRepository()
        return self._permission_repository

    @property
    def register_use_case(self) -> RegisterUserUseCase:
        if self._register_use_case is None:
            self._register_use_case = RegisterUserUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
            )
        return self._register_use_case

    @property
    def login_use_case(self) -> LoginUserUseCase:
        if self._login_use_case is None:
            self._login_use_case = LoginUserUseCase(
                user_repository=self.user_repository,
                password_hasher=self.password_hasher,
                jwt_provider=self.jwt_provider,
            )
        return self._login_use_case

    @property
    def forgot_password_use_case(self) -> ForgotPasswordUseCase:
        if self._forgot_password_use_case is None:
            self._forgot_password_use_case = ForgotPasswordUseCase(
                user_repository=self.user_repository,
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
            )
        return self._resend_verification_use_case

    @property
    def auth_controller(self) -> AuthController:
        if self._auth_controller is None:
            self._auth_controller = AuthController(
                register_use_case=self.register_use_case,
                login_use_case=self.login_use_case,
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


_container_instance: Container | None = None


def get_container() -> Container:
    global _container_instance
    if _container_instance is None:
        _container_instance = Container()
    return _container_instance
