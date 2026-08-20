from abc import ABC

import pytest
from src.domain.repositories.user_repository import UserRepository


def test_user_repository_is_abstract():
    assert issubclass(UserRepository, ABC)

    with pytest.raises(TypeError):
        UserRepository()


def test_user_repository_has_required_methods():
    required_methods = ['save', 'find_by_id', 'find_by_email', 'find_by_tenant', 'delete']

    for method_name in required_methods:
        assert hasattr(UserRepository, method_name)

        method = getattr(UserRepository, method_name)
        assert getattr(method, '__isabstractmethod__', False) is True


def test_user_repository_method_signatures():
    pass
