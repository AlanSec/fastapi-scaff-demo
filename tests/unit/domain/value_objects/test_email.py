import pytest
from src.domain.value_objects.email import Email


def test_email_creation_with_valid_email():
    email = Email("user@example.com")
    assert str(email) == "user@example.com"


def test_email_creation_with_invalid_email_raises_value_error():
    with pytest.raises(ValueError, match="invalid email"):
        Email("invalid-email")


def test_email_equality():
    email1 = Email("user@example.com")
    email2 = Email("user@example.com")
    email3 = Email("other@example.com")

    assert email1 == email2
    assert email1 != email3
    assert hash(email1) == hash(email2)


def test_email_normalization():
    email = Email("USER@EXAMPLE.COM")
    assert str(email) == "user@example.com"


def test_email_is_immutable():
    email = Email("user@example.com")

    with pytest.raises(AttributeError):
        email.value = "other@example.com"
