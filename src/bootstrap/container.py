from dataclasses import dataclass

from src.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.security.jwt_provider import JWTProviderImpl
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.use_cases.password_use_case import (
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
    ChangePasswordUseCase,
)
from src.application.use_cases.verify_use_case import VerifyEmailUseCase, ResendVerificationUseCase
from src.api.controllers.auth_controller import AuthController
from src.api.controllers.password_controller import PasswordController, VerifyController


@dataclass
class AppConfig:
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class Container:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
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

    @property
    def config(self) -> AppConfig:
        if self._config is None:
            self._config = AppConfig()
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