from uuid import uuid4

import pytest
from src.application.dto.auth_dto import (
    LoginUserInputDTO,
    LoginUserOutputDTO,
    RegisterUserInputDTO,
    RegisterUserOutputDTO,
)


class TestRegisterUserInputDTO:
    def test_create_register_user_input_dto(self):
        email = "test@example.com"
        password = "password123"
        tenant_id = uuid4()

        dto = RegisterUserInputDTO(
            email=email,
            password=password,
            tenant_id=tenant_id
        )

        assert dto.email == email
        assert dto.password == password
        assert dto.tenant_id == tenant_id

    def test_register_user_input_dto_is_immutable(self):
        tenant_id = uuid4()
        dto = RegisterUserInputDTO(
            email="test@example.com",
            password="password123",
            tenant_id=tenant_id
        )

        with pytest.raises(AttributeError):
            dto.email = "changed@example.com"


class TestRegisterUserOutputDTO:
    def test_create_register_user_output_dto(self):
        user_id = uuid4()
        tenant_id = uuid4()

        dto = RegisterUserOutputDTO(
            user_id=user_id,
            email="test@example.com",
            tenant_id=tenant_id,
            is_verified=False
        )

        assert dto.user_id == user_id
        assert dto.email == "test@example.com"
        assert dto.tenant_id == tenant_id
        assert dto.is_verified is False

    def test_register_user_output_dto_is_immutable(self):
        dto = RegisterUserOutputDTO(
            user_id=uuid4(),
            email="test@example.com",
            tenant_id=uuid4(),
            is_verified=False
        )

        with pytest.raises(AttributeError):
            dto.email = "changed@example.com"


class TestLoginUserInputDTO:
    def test_create_login_user_input_dto(self):
        email = "test@example.com"
        password = "password123"
        tenant_id = uuid4()

        dto = LoginUserInputDTO(
            email=email,
            password=password,
            tenant_id=tenant_id
        )

        assert dto.email == email
        assert dto.password == password
        assert dto.tenant_id == tenant_id

    def test_login_user_input_dto_is_immutable(self):
        tenant_id = uuid4()
        dto = LoginUserInputDTO(
            email="test@example.com",
            password="password123",
            tenant_id=tenant_id
        )

        with pytest.raises(AttributeError):
            dto.password = "changed"


class TestLoginUserOutputDTO:
    def test_create_login_user_output_dto(self):
        user_id = uuid4()
        tenant_id = uuid4()

        dto = LoginUserOutputDTO(
            user_id=user_id,
            email="test@example.com",
            tenant_id=tenant_id,
            access_token="access_token_value",
            refresh_token="refresh_token_value",
            expires_in=1800
        )

        assert dto.user_id == user_id
        assert dto.email == "test@example.com"
        assert dto.tenant_id == tenant_id
        assert dto.access_token == "access_token_value"
        assert dto.refresh_token == "refresh_token_value"
        assert dto.expires_in == 1800

    def test_login_user_output_dto_is_immutable(self):
        dto = LoginUserOutputDTO(
            user_id=uuid4(),
            email="test@example.com",
            tenant_id=uuid4(),
            access_token="access_token_value",
            refresh_token="refresh_token_value",
            expires_in=1800
        )

        with pytest.raises(AttributeError):
            dto.access_token = "changed"
