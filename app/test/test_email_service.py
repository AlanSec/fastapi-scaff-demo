"""
邮件服务单元测试
测试EmailService类的功能
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.email import EmailService


class TestEmailService:
    """测试EmailService类"""

    @pytest.fixture
    def email_service(self):
        """创建EmailService实例"""
        return EmailService()

    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service):
        """测试发送邮件成功"""
        # 模拟_send_sync_email方法
        with patch.object(email_service, '_send_sync_email') as mock_send_sync:
            mock_send_sync.return_value = True

            # 发送测试邮件
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="测试主题",
                html_content="<h1>测试内容</h1>"
            )

            # 验证结果
            assert result is True
            mock_send_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_failure(self, email_service):
        """测试发送邮件失败"""
        # 模拟_send_sync_email方法抛出异常
        with patch.object(email_service, '_send_sync_email') as mock_send_sync:
            mock_send_sync.side_effect = Exception("SMTP连接失败")

            # 发送测试邮件
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="测试主题",
                html_content="<h1>测试内容</h1>"
            )

            # 验证结果
            assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_email(self, email_service):
        """测试发送验证邮件"""
        with patch.object(email_service, 'send_email') as mock_send_email:
            mock_send_email.return_value = True

            result = await email_service.send_verification_email(
                to_email="test@example.com",
                verification_token="test-token-123",
                username="testuser"
            )

            assert result is True
            mock_send_email.assert_called_once()
            # 验证邮件内容包含令牌
            call_args = mock_send_email.call_args
            # 使用 kwargs 属性获取关键字参数
            assert "test-token-123" in call_args.kwargs.get('html_content', '') or \
                   "test-token-123" in str(call_args)

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, email_service):
        """测试发送密码重置邮件"""
        with patch.object(email_service, 'send_email') as mock_send_email:
            mock_send_email.return_value = True

            result = await email_service.send_password_reset_email(
                to_email="test@example.com",
                reset_token="reset-token-456",
                username="testuser"
            )

            assert result is True
            mock_send_email.assert_called_once()
            # 验证邮件内容包含重置令牌
            call_args = mock_send_email.call_args
            assert "reset-token-456" in call_args.kwargs.get('html_content', '') or \
                   "reset-token-456" in str(call_args)

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, email_service):
        """测试发送欢迎邮件"""
        with patch.object(email_service, 'send_email') as mock_send_email:
            mock_send_email.return_value = True

            result = await email_service.send_welcome_email(
                to_email="test@example.com",
                username="testuser"
            )

            assert result is True
            mock_send_email.assert_called_once()
            # 验证邮件内容包含用户名
            call_args = mock_send_email.call_args
            assert "testuser" in call_args.kwargs.get('html_content', '') or \
                   "testuser" in str(call_args)