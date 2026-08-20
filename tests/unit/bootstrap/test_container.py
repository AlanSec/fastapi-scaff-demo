import pytest
from src.api.controllers.auth_controller import AuthController
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.bootstrap.container import Container, get_container
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_user_repository import SQLModelUserRepository
from src.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from src.infrastructure.security.jwt_provider import JWTProviderImpl


class TestContainer:
    @pytest.fixture
    def container(self):
        return Container()

    def test_container_has_password_hasher(self, container):
        assert container.password_hasher is not None
        assert isinstance(container.password_hasher, BcryptPasswordHasher)

    def test_container_has_jwt_provider(self, container):
        assert container.jwt_provider is not None
        assert isinstance(container.jwt_provider, JWTProviderImpl)

    def test_container_has_rate_limiter(self, container):
        from src.infrastructure.security.redis_rate_limiter import RedisRateLimiter
        assert isinstance(container.rate_limiter, RedisRateLimiter)

    def test_container_has_email_sender(self, container):
        assert container.email_sender is not None

    def test_container_has_user_repository(self, container):
        assert container.user_repository is not None
        assert isinstance(container.user_repository, SQLModelUserRepository)

    def test_container_has_register_use_case(self, container):
        assert container.register_use_case is not None
        assert isinstance(container.register_use_case, RegisterUserUseCase)

    def test_container_has_login_use_case(self, container):
        assert container.login_use_case is not None
        assert isinstance(container.login_use_case, LoginUserUseCase)

    def test_container_has_auth_controller(self, container):
        assert container.auth_controller is not None
        assert isinstance(container.auth_controller, AuthController)

    def test_container_has_all_controllers(self, container):
        """lifespan 启动时会访问这些 controller，缺失会导致启动崩溃"""
        assert container.tenant_controller is not None
        assert container.role_controller is not None
        assert container.permission_controller is not None
        assert container.user_admin_controller is not None
        assert container.password_controller is not None
        assert container.verify_controller is not None

    def test_container_has_config(self, container):
        assert container.config is not None


class TestContainerDependencyResolution:
    @pytest.fixture
    def container(self):
        return Container()

    def test_register_use_case_uses_correct_dependencies(self, container):
        use_case = container.register_use_case
        assert use_case.user_repository is container.user_repository
        assert use_case.password_hasher is container.password_hasher

    def test_login_use_case_uses_correct_dependencies(self, container):
        use_case = container.login_use_case
        assert use_case.user_repository is container.user_repository
        assert use_case.password_hasher is container.password_hasher
        assert use_case.jwt_provider is container.jwt_provider

    def test_auth_controller_uses_correct_dependencies(self, container):
        controller = container.auth_controller
        assert controller._register_use_case is container.register_use_case
        assert controller._login_use_case is container.login_use_case


class TestGetContainer:
    def test_get_container_returns_same_instance(self):
        c1 = get_container()
        c2 = get_container()
        assert c1 is c2
