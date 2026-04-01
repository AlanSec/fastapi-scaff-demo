import pytest
from src.domain.value_objects.password import Password, HashedPassword


def test_password_creation_with_valid_password():
    password = Password("ValidPass123")
    assert isinstance(password, Password)


def test_password_creation_with_short_password_raises_value_error():
    with pytest.raises(ValueError, match="password must be at least"):
        Password("short")


def test_password_creation_with_weak_password_raises_value_error():
    with pytest.raises(ValueError, match="password must contain at least one uppercase"):
        Password("lowercase123")
    
    with pytest.raises(ValueError, match="password must contain at least one lowercase"):
        Password("UPPERCASE123")
    
    with pytest.raises(ValueError, match="password must contain at least one digit"):
        Password("NoNumbers")


def test_password_equality():
    password1 = Password("ValidPass123")
    password2 = Password("ValidPass123")
    password3 = Password("Different123")
    
    assert password1 == password2
    assert password1 != password3


def test_hashed_password_creation():
    hashed = HashedPassword("$2b$12$somehashedvalue")
    assert isinstance(hashed, HashedPassword)
    assert str(hashed) == "$2b$12$somehashedvalue"


def test_hashed_password_equality():
    hash1 = HashedPassword("$2b$12$hash1")
    hash2 = HashedPassword("$2b$12$hash1")
    hash3 = HashedPassword("$2b$12$hash2")
    
    assert hash1 == hash2
    assert hash1 != hash3


def test_password_is_immutable():
    password = Password("ValidPass123")
    
    with pytest.raises(AttributeError):
        password.value = "newpassword"


def test_hashed_password_is_immutable():
    hashed = HashedPassword("$2b$12$hash")
    
    with pytest.raises(AttributeError):
        hashed.value = "newhash"