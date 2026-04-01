"""Bcrypt 密码哈希器测试"""
import pytest

from src.domain.entities.auth import PasswordHasher
from src.domain.value_objects.password import Password, HashedPassword
from src.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher


def test_bcrypt_password_hasher_is_implementation():
    """测试 BcryptPasswordHasher 实现 PasswordHasher 接口"""
    assert issubclass(BcryptPasswordHasher, PasswordHasher)


def test_hash_password():
    """测试密码哈希"""
    hasher = BcryptPasswordHasher()
    password = Password("TestPass123")
    
    hashed = hasher.hash(password)
    
    assert isinstance(hashed, HashedPassword)
    assert hashed.value != "TestPass123"


def test_verify_correct_password():
    """测试验证正确密码"""
    hasher = BcryptPasswordHasher()
    password = Password("TestPass123")
    
    hashed = hasher.hash(password)
    result = hasher.verify(password, hashed)
    
    assert result is True


def test_verify_incorrect_password():
    """测试验证错误密码"""
    hasher = BcryptPasswordHasher()
    password = Password("TestPass123")
    wrong_password = Password("WrongPass456")
    
    hashed = hasher.hash(password)
    result = hasher.verify(wrong_password, hashed)
    
    assert result is False