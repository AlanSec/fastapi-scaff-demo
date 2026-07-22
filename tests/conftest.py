import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from typing import AsyncGenerator
from datetime import datetime, timedelta, timezone

from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_password_hasher():
    return MagicMock()


@pytest.fixture
def mock_jwt_provider():
    return AsyncMock()


@pytest.fixture
def sample_tenant_id():
    return uuid4()


@pytest.fixture
def sample_email():
    return Email("test@example.com")


@pytest.fixture
def sample_password():
    return "Password123"


@pytest.fixture
def hashed_password():
    return HashedPassword("")


@pytest.fixture
def utc_now():
    return datetime.now(timezone.utc)


@pytest.fixture
def future_datetime(utc_now):
    return utc_now + timedelta(minutes=30)


@pytest.fixture
def past_datetime(utc_now):
    return utc_now - timedelta(minutes=30)
