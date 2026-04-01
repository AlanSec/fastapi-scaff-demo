import pytest
from abc import ABC

from src.domain.services.interfaces import AuthService, PermissionService


def test_auth_service_is_abstract():
    assert issubclass(AuthService, ABC)

    with pytest.raises(TypeError):
        AuthService()


def test_auth_service_has_required_methods():
    required_methods = ['authenticate', 'register', 'verify_token', 'refresh_token']

    for method_name in required_methods:
        assert hasattr(AuthService, method_name)
        method = getattr(AuthService, method_name)
        assert getattr(method, '__isabstractmethod__', False) is True


def test_permission_service_is_abstract():
    assert issubclass(PermissionService, ABC)

    with pytest.raises(TypeError):
        PermissionService()


def test_permission_service_has_required_methods():
    required_methods = ['check_permission', 'get_user_permissions', 'assign_role', 'revoke_role']

    for method_name in required_methods:
        assert hasattr(PermissionService, method_name)
        method = getattr(PermissionService, method_name)
        assert getattr(method, '__isabstractmethod__', False) is True