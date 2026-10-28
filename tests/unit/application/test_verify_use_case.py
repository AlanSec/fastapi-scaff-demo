"""邮箱验证流程 UseCase 测试——使用真实 InMemory 仓储。"""
from uuid import uuid4

import pytest
from src.application.dto.password_dto import (
    ResendVerificationInputDTO,
    VerifyEmailInputDTO,
)
from src.application.use_cases.verify_use_case import (
    GENERIC_VERIFY_MESSAGE,
    ResendVerificationUseCase,
    VerifyEmailUseCase,
)
from src.domain.entities.user import User
from src.domain.services.email_interfaces import EmailSender
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository


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


def _extract_token_from_email(sender: RecordingEmailSender) -> str:
    """从发送的邮件正文中提取 token"""
    assert sender.sent, "no email was sent"
    body = sender.sent[-1][2]
    return body.split(": ", 1)[1].strip()


@pytest.fixture
def repo():
    return InMemoryUserRepository()


@pytest.fixture
def email_sender():
    return RecordingEmailSender()


@pytest.mark.asyncio
async def test_resend_stores_token_sends_email_and_verify_success(repo, email_sender):
    user = _make_user(repo)
    await repo.save(user)

    resend = ResendVerificationUseCase(repo, email_sender)
    result = await resend.execute(ResendVerificationInputDTO(email="test@example.com"))

    # 响应体不得泄露 token
    assert result.message == GENERIC_VERIFY_MESSAGE
    assert "verify_" not in result.message

    token = _extract_token_from_email(email_sender)
    assert token.startswith("verify_")
    assert email_sender.sent[-1][0] == "test@example.com"

    # token 已存储，可通过仓储查回
    found = await repo.find_by_verification_token(token)
    assert found is not None
    assert found.id == user.id
    assert found.is_verified is False

    verify = VerifyEmailUseCase(repo)
    verify_result = await verify.execute(VerifyEmailInputDTO(token=token))
    assert verify_result.is_verified is True

    updated = await repo.find_by_id(user.id, user.tenant_id)
    assert updated.is_verified is True
    # 验证后 token 应被清除
    assert await repo.find_by_verification_token(token) is None


@pytest.mark.asyncio
async def test_resend_already_verified(repo, email_sender):
    user = _make_user(repo).verify()
    await repo.save(user)

    resend = ResendVerificationUseCase(repo, email_sender)
    result = await resend.execute(ResendVerificationInputDTO(email="test@example.com"))
    assert result.message == "Email is already verified"
    assert email_sender.sent == []


@pytest.mark.asyncio
async def test_resend_user_not_found(repo, email_sender):
    resend = ResendVerificationUseCase(repo, email_sender)
    result = await resend.execute(ResendVerificationInputDTO(email="nobody@example.com"))
    assert result.message == GENERIC_VERIFY_MESSAGE
    assert email_sender.sent == []


@pytest.mark.asyncio
async def test_verify_invalid_token(repo):
    verify = VerifyEmailUseCase(repo)
    with pytest.raises(ValueError, match="Invalid verification token"):
        await verify.execute(VerifyEmailInputDTO(token="verify_bogus"))
