"""密码流程 UseCase 测试——使用真实 InMemory 仓储 + 真实假 hasher，
确保实体字段不匹配等 bug 能被立即暴露（而非被 MagicMock 掩盖）。"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from src.application.dto.password_dto import (
    ChangePasswordInputDTO,
    ForgotPasswordInputDTO,
    ResetPasswordInputDTO,
)
from src.application.use_cases.password_use_case import (
    GENERIC_FORGOT_MESSAGE,
    ChangePasswordUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
)
from src.domain.entities.user import User
from src.domain.services.email_interfaces import EmailSender
from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword, Password
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository


class FakePasswordHasher(PasswordHasher):
    """确定性假 hasher：hash 可逆、verify 可校验"""

    def hash(self, password: Password) -> HashedPassword:
        return HashedPassword(f"hashed:{password.value}")

    def verify(self, password: Password, hashed: HashedPassword) -> bool:
        return hashed.value == f"hashed:{password.value}"


class RecordingEmailSender(EmailSender):
    """记录发送的邮件（测试用）"""

    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


def _make_user(repo: InMemoryUserRepository, email: str = "test@example.com") -> User:
    user = User.create(
        email=Email(email),
        password=HashedPassword("hashed:Password123"),
        tenant_id=uuid4(),
    )
    return user


@pytest.fixture
def repo():
    return InMemoryUserRepository()


@pytest.fixture
def hasher():
    return FakePasswordHasher()


@pytest.fixture
def email_sender():
    return RecordingEmailSender()


def _extract_token_from_email(sender: RecordingEmailSender) -> str:
    """从发送的邮件正文中提取 token"""
    assert sender.sent, "no email was sent"
    body = sender.sent[-1][2]
    return body.split(": ", 1)[1].strip().split("\n")[0]


@pytest.mark.asyncio
async def test_forgot_password_sends_email_and_stores_token(repo, email_sender):
    user = _make_user(repo)
    await repo.save(user)

    use_case = ForgotPasswordUseCase(repo, email_sender)
    result = await use_case.execute(ForgotPasswordInputDTO(email="test@example.com"))

    # 响应体不得泄露 token
    assert result.message == GENERIC_FORGOT_MESSAGE
    assert "reset_" not in result.message

    # token 通过邮件发送，且已存储
    token = _extract_token_from_email(email_sender)
    assert token.startswith("reset_")
    assert email_sender.sent[-1][0] == "test@example.com"

    found = await repo.find_by_reset_token(token)
    assert found is not None
    assert found.id == user.id
    assert found.reset_token == token
    assert found.reset_token_expires_at is not None


@pytest.mark.asyncio
async def test_forgot_password_returns_generic_message_when_user_not_found(repo, email_sender):
    use_case = ForgotPasswordUseCase(repo, email_sender)
    result = await use_case.execute(ForgotPasswordInputDTO(email="nobody@example.com"))
    assert result.message == GENERIC_FORGOT_MESSAGE
    assert email_sender.sent == []


@pytest.mark.asyncio
async def test_reset_password_success(repo, hasher, email_sender):
    user = _make_user(repo)
    await repo.save(user)

    forgot = ForgotPasswordUseCase(repo, email_sender)
    await forgot.execute(ForgotPasswordInputDTO(email="test@example.com"))
    token = _extract_token_from_email(email_sender)

    reset = ResetPasswordUseCase(repo, hasher)
    result = await reset.execute(ResetPasswordInputDTO(token=token, new_password="NewPass456"))

    assert result.message == "Password reset successful"
    updated = await repo.find_by_id(user.id)
    assert hasher.verify(Password("NewPass456"), updated.password)
    # token 使用后应被清除
    assert await repo.find_by_reset_token(token) is None


@pytest.mark.asyncio
async def test_reset_password_invalid_token(repo, hasher):
    reset = ResetPasswordUseCase(repo, hasher)
    with pytest.raises(ValueError, match="Invalid or expired reset token"):
        await reset.execute(ResetPasswordInputDTO(token="reset_bogus", new_password="NewPass456"))


@pytest.mark.asyncio
async def test_reset_password_expired_token(repo, hasher):
    user = _make_user(repo)
    user = user.with_reset_token(
        "reset_expired", datetime.now() - timedelta(minutes=1)
    )
    await repo.save(user)

    reset = ResetPasswordUseCase(repo, hasher)
    with pytest.raises(ValueError, match="Invalid or expired reset token"):
        await reset.execute(ResetPasswordInputDTO(token="reset_expired", new_password="NewPass456"))


@pytest.mark.asyncio
async def test_change_password_success(repo, hasher):
    user = _make_user(repo)
    await repo.save(user)

    change = ChangePasswordUseCase(repo, hasher)
    result = await change.execute(
        ChangePasswordInputDTO(current_password="Password123", new_password="NewPass456"),
        user.id,
    )

    assert result.message == "Password changed successfully"
    updated = await repo.find_by_id(user.id)
    assert hasher.verify(Password("NewPass456"), updated.password)


@pytest.mark.asyncio
async def test_change_password_wrong_current(repo, hasher):
    user = _make_user(repo)
    await repo.save(user)

    change = ChangePasswordUseCase(repo, hasher)
    with pytest.raises(ValueError, match="Current password is incorrect"):
        await change.execute(
            ChangePasswordInputDTO(current_password="WrongPass1", new_password="NewPass456"),
            user.id,
        )


@pytest.mark.asyncio
async def test_change_password_user_not_found(repo, hasher):
    change = ChangePasswordUseCase(repo, hasher)
    with pytest.raises(ValueError, match="User not found"):
        await change.execute(
            ChangePasswordInputDTO(current_password="Password123", new_password="NewPass456"),
            uuid4(),
        )
