"""
验证API集成测试
测试邮箱验证相关端点
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.user import User


class TestVerifyAPI:
    """测试验证API端点"""

    def test_verify_email_success(self, test_client):
        """测试邮箱验证成功"""
        # 模拟验证服务
        with patch('app.api.v1.verify.VerificationService.verify_email_token') as mock_verify:
            # 模拟验证成功
            mock_user = AsyncMock()
            mock_user.id = 1
            mock_verify.return_value = mock_user

            # 发送验证请求
            response = test_client.get(
                "/api/v1/auth/verify/email",
                params={"token": "valid-verification-token"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "邮箱验证成功" in data["message"]

            # 验证服务被调用
            mock_verify.assert_called_once_with("valid-verification-token")

    def test_verify_email_invalid_token(self, test_client):
        """测试邮箱验证使用无效令牌"""
        with patch('app.api.v1.verify.VerificationService.verify_email_token') as mock_verify:
            # 模拟验证失败
            mock_verify.return_value = None

            # 发送验证请求
            response = test_client.get(
                "/api/v1/auth/verify/email",
                params={"token": "invalid-token"}
            )

            # 验证响应：应该返回400错误
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "无效或过期的验证令牌" in data["detail"]

    def test_resend_verification_success(self, test_client):
        """测试重新发送验证邮件成功"""
        # 先创建一个未验证的用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "resend@example.com",
                    "username": "resenduser",
                    "password": "Password123!"
                }
            )

        # 模拟邮件发送
        with patch('app.api.v1.verify.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            # 发送重新发送验证邮件请求
            response = test_client.post(
                "/api/v1/auth/verify/resend",
                json={"email": "resend@example.com"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "验证邮件已重新发送" in data["message"]

            # 验证邮件服务被调用
            mock_send_verification.assert_called_once()

    def test_resend_verification_email_not_found(self, test_client):
        """测试重新发送验证邮件（邮箱不存在）"""
        # 模拟邮件发送
        with patch('app.api.v1.verify.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            # 发送重新发送验证邮件请求（邮箱不存在）
            response = test_client.post(
                "/api/v1/auth/verify/resend",
                json={"email": "nonexistent@example.com"}
            )

            # 验证响应：出于安全考虑，即使邮箱不存在也返回成功消息
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "如果该邮箱已注册且未验证" in data["message"]

            # 验证邮件服务未被调用（因为用户不存在）
            mock_send_verification.assert_not_called()

    def test_resend_verification_already_verified(self, test_client):
        """测试重新发送验证邮件（已验证的用户）"""
        # 创建一个用户并验证（在真实场景中需要先验证）
        # 这里我们主要测试API端点
        pass

    def test_resend_verification_email_send_failure(self, test_client):
        """测试重新发送验证邮件发送失败"""
        # 先创建一个未验证的用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "failresend@example.com",
                    "username": "failresend",
                    "password": "Password123!"
                }
            )

        # 模拟邮件发送失败
        with patch('app.api.v1.verify.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = False

            # 发送重新发送验证邮件请求
            response = test_client.post(
                "/api/v1/auth/verify/resend",
                json={"email": "failresend@example.com"}
            )

            # 验证响应：应该返回500错误
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "邮件发送失败" in data["detail"]

    def test_get_verification_status_not_authenticated(self, test_client):
        """测试获取验证状态（未认证用户）"""
        # 发送获取验证状态请求（未登录）
        response = test_client.get("/api/v1/auth/verify/status")

        # 验证响应：应该返回401未授权
        # 注意：实际的实现使用current_user依赖项
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "需要登录" in data["detail"]

    def test_send_test_email_not_admin(self, test_client):
        """测试发送测试邮件（非管理员）"""
        # 发送测试邮件请求（非管理员）
        response = test_client.post(
            "/api/v1/auth/verify/send-test-email",
            params={"email": "test@example.com"}
        )

        # 验证响应：应该返回401或403（需要管理员权限）
        # 注意：实际的实现需要管理员权限
        assert response.status_code in [401, 403]
        if response.status_code == 403:
            data = response.json()
            assert "detail" in data
            assert "需要管理员角色" in data["detail"]

    def test_resend_verification_user_has_no_token(self, test_client):
        """测试重新发送验证邮件（用户没有令牌）"""
        # 先创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "notoken@example.com",
                    "username": "notoken",
                    "password": "Password123!"
                }
            )

        # 模拟验证服务创建新令牌
        with patch('app.api.v1.verify.VerificationService.create_verification_token') as mock_create_token, \
             patch('app.api.v1.verify.email_service.send_verification_email') as mock_send_verification:

            mock_create_token.return_value = "new-token-123"
            mock_send_verification.return_value = True

            # 发送重新发送验证邮件请求
            response = test_client.post(
                "/api/v1/auth/verify/resend",
                json={"email": "notoken@example.com"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

            # 验证服务被调用（创建新令牌）
            mock_create_token.assert_called_once()
            mock_send_verification.assert_called_once()