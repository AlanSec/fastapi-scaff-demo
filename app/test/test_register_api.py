"""
注册API集成测试
测试用户注册相关端点
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.user import User


class TestRegisterAPI:
    """测试注册API端点"""

    def test_register_success(self, test_client):
        """测试注册成功"""
        # 模拟邮件服务
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification, \
             patch('app.api.v1.register.email_service.send_welcome_email') as mock_send_welcome:

            mock_send_verification.return_value = True
            mock_send_welcome.return_value = True

            # 发送注册请求
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "Password123!"
                }
            )

            # 验证响应
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@example.com"
            assert data["username"] == "newuser"
            assert "id" in data
            assert "message" in data
            assert "注册成功" in data["message"]

            # 验证邮件服务被调用
            mock_send_verification.assert_called_once()
            mock_send_welcome.assert_called_once()

    def test_register_duplicate_email(self, test_client):
        """测试注册重复邮箱"""
        # 先创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            # 第一次注册
            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "duplicate@example.com",
                    "username": "user1",
                    "password": "Password123!"
                }
            )

            # 第二次使用相同邮箱注册
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "duplicate@example.com",
                    "username": "user2",
                    "password": "Password123!"
                }
            )

            # 验证响应：应该返回400错误
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "邮箱已被注册" in data["detail"]

    def test_register_duplicate_username(self, test_client):
        """测试注册重复用户名"""
        # 先创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            # 第一次注册
            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "user1@example.com",
                    "username": "sameusername",
                    "password": "Password123!"
                }
            )

            # 第二次使用相同用户名注册
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "user2@example.com",
                    "username": "sameusername",
                    "password": "Password123!"
                }
            )

            # 验证响应：应该返回400错误
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "用户名已被使用" in data["detail"]

    def test_register_weak_password(self, test_client):
        """测试注册弱密码"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "123"  # 太短
            }
        )

        # 验证响应：应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_register_invalid_email(self, test_client):
        """测试注册无效邮箱"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "Password123!"
            }
        )

        # 验证响应：应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_check_email_available(self, test_client):
        """测试检查邮箱可用性"""
        # 第一次检查（应该可用）
        response = test_client.get(
            "/api/v1/auth/register/check-email",
            params={"email": "available@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "available@example.com"
        assert data["available"] is True

        # 创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "taken@example.com",
                    "username": "takenuser",
                    "password": "Password123!"
                }
            )

        # 第二次检查（应该不可用）
        response = test_client.get(
            "/api/v1/auth/register/check-email",
            params={"email": "taken@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "taken@example.com"
        assert data["available"] is False

    def test_check_username_available(self, test_client):
        """测试检查用户名可用性"""
        # 第一次检查（应该可用）
        response = test_client.get(
            "/api/v1/auth/register/check-username",
            params={"username": "availableuser"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "availableuser"
        assert data["available"] is True

        # 创建一个用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "user@example.com",
                    "username": "takenusername",
                    "password": "Password123!"
                }
            )

        # 第二次检查（应该不可用）
        response = test_client.get(
            "/api/v1/auth/register/check-username",
            params={"username": "takenusername"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "takenusername"
        assert data["available"] is False

    def test_register_with_email_send_failure(self, test_client):
        """测试注册时邮件发送失败"""
        # 模拟邮件发送失败
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification, \
             patch('app.api.v1.register.email_service.send_welcome_email') as mock_send_welcome:

            mock_send_verification.return_value = False  # 邮件发送失败
            mock_send_welcome.return_value = False

            # 发送注册请求
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "emailfail@example.com",
                    "username": "emailfail",
                    "password": "Password123!"
                }
            )

            # 验证响应：即使邮件发送失败，注册也应成功
            # 用户可以在之后重新请求发送验证邮件
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "emailfail@example.com"
            assert "注册成功" in data["message"]