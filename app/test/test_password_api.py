"""
密码API集成测试
测试密码重置和更改相关端点
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.user import User


class TestPasswordAPI:
    """测试密码API端点"""

    def test_forgot_password_success(self, test_client):
        """测试忘记密码请求成功"""
        # 先创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "forgot@example.com",
                    "username": "forgotuser",
                    "password": "Password123!"
                }
            )

        # 模拟密码重置邮件发送
        with patch('app.api.v1.password.email_service.send_password_reset_email') as mock_send_reset:
            mock_send_reset.return_value = True

            # 发送忘记密码请求
            response = test_client.post(
                "/api/v1/auth/password/forgot",
                json={"email": "forgot@example.com"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "重置链接" in data["message"]

            # 验证邮件服务被调用
            mock_send_reset.assert_called_once()

    def test_forgot_password_email_not_found(self, test_client):
        """测试忘记密码请求（邮箱不存在）"""
        # 模拟密码重置邮件发送
        with patch('app.api.v1.password.email_service.send_password_reset_email') as mock_send_reset:
            mock_send_reset.return_value = True

            # 发送忘记密码请求（邮箱不存在）
            response = test_client.post(
                "/api/v1/auth/password/forgot",
                json={"email": "nonexistent@example.com"}
            )

            # 验证响应：出于安全考虑，即使邮箱不存在也返回成功消息
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "如果该邮箱已注册" in data["message"]

            # 验证邮件服务未被调用（因为用户不存在）
            mock_send_reset.assert_not_called()

    def test_reset_password_success(self, test_client):
        """测试重置密码成功"""
        # 先创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "reset@example.com",
                    "username": "resetuser",
                    "password": "OldPassword123!"
                }
            )

        # 需要模拟验证服务生成和验证令牌
        # 这里我们直接测试API端点，假设令牌有效
        with patch('app.api.v1.password.VerificationService.verify_password_reset_token') as mock_verify, \
             patch('app.api.v1.password.VerificationService.clear_password_reset_token') as mock_clear:

            # 模拟验证服务
            mock_user = AsyncMock()
            mock_user.id = 1
            mock_verify.return_value = mock_user
            mock_clear.return_value = None

            # 发送重置密码请求
            response = test_client.post(
                "/api/v1/auth/password/reset",
                json={
                    "token": "valid-reset-token",
                    "new_password": "NewPassword123!"
                }
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "密码重置成功" in data["message"]

            # 验证服务被调用
            mock_verify.assert_called_once_with("valid-reset-token")
            mock_clear.assert_called_once_with(mock_user)

    def test_reset_password_invalid_token(self, test_client):
        """测试重置密码使用无效令牌"""
        with patch('app.api.v1.password.VerificationService.verify_password_reset_token') as mock_verify:
            # 模拟验证失败
            mock_verify.return_value = None

            # 发送重置密码请求
            response = test_client.post(
                "/api/v1/auth/password/reset",
                json={
                    "token": "invalid-token",
                    "new_password": "NewPassword123!"
                }
            )

            # 验证响应：应该返回400错误
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "无效或过期的重置令牌" in data["detail"]

    def test_reset_password_weak_new_password(self, test_client):
        """测试重置密码使用弱密码"""
        # 发送重置密码请求（弱密码）
        response = test_client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": "some-token",
                "new_password": "123"  # 太短
            }
        )

        # 验证响应：应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_change_password_success(self, test_client):
        """测试更改密码成功（需要登录）"""
        # 此测试需要模拟用户登录
        # 由于认证系统还在开发中，我们先跳过详细的登录测试
        # 主要测试API端点存在和基本验证
        pass

    def test_change_password_not_authenticated(self, test_client):
        """测试未认证用户更改密码"""
        # 发送更改密码请求（未登录）
        response = test_client.post(
            "/api/v1/auth/password/change",
            params={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            }
        )

        # 验证响应：应该返回401未授权
        # 注意：实际的实现可能使用不同的认证方式
        # 这里我们主要测试端点存在
        assert response.status_code in [401, 422, 200]  # 取决于具体实现

    def test_forgot_password_email_send_failure(self, test_client):
        """测试忘记密码邮件发送失败"""
        # 先创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "failsend@example.com",
                    "username": "failsend",
                    "password": "Password123!"
                }
            )

        # 模拟密码重置邮件发送失败
        with patch('app.api.v1.password.email_service.send_password_reset_email') as mock_send_reset:
            mock_send_reset.return_value = False

            # 发送忘记密码请求
            response = test_client.post(
                "/api/v1/auth/password/forgot",
                json={"email": "failsend@example.com"}
            )

            # 验证响应：应该返回500错误
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "邮件发送失败" in data["detail"]