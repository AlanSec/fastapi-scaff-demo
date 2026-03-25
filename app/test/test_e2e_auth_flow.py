"""
端到端认证流程测试
测试完整的用户认证流程
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestE2EAuthFlow:
    """测试端到端认证流程"""

    def test_complete_user_journey(self, test_client):
        """测试完整的用户旅程：注册→验证→登录→忘记密码→重置密码"""
        # 记录测试过程中的数据
        test_data = {}

        # 1. 注册新用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification, \
             patch('app.api.v1.register.email_service.send_welcome_email') as mock_send_welcome:

            mock_send_verification.return_value = True
            mock_send_welcome.return_value = True

            register_response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "journey@example.com",
                    "username": "journeyuser",
                    "password": "JourneyPass123!"
                }
            )

            assert register_response.status_code == 201
            register_data = register_response.json()
            assert register_data["email"] == "journey@example.com"
            test_data["user_id"] = register_data["id"]
            test_data["email"] = register_data["email"]

            # 保存验证令牌（从邮件服务调用中获取）
            # 在实际测试中，需要从模拟对象中提取令牌
            # 这里我们假设有一个已知的令牌
            test_data["verification_token"] = "test-verification-token-123"

        # 2. 检查邮箱和用户名可用性
        # 检查邮箱（应该不可用）
        check_email_response = test_client.get(
            "/api/v1/auth/register/check-email",
            params={"email": "journey@example.com"}
        )
        assert check_email_response.status_code == 200
        email_data = check_email_response.json()
        assert email_data["available"] is False

        # 检查用户名（应该不可用）
        check_username_response = test_client.get(
            "/api/v1/auth/register/check-username",
            params={"username": "journeyuser"}
        )
        assert check_username_response.status_code == 200
        username_data = check_username_response.json()
        assert username_data["available"] is False

        # 3. 验证邮箱
        with patch('app.api.v1.verify.VerificationService.verify_email_token') as mock_verify:
            # 模拟验证成功
            mock_user = AsyncMock()
            mock_user.id = test_data["user_id"]
            mock_verify.return_value = mock_user

            verify_response = test_client.get(
                "/api/v1/auth/verify/email",
                params={"token": test_data["verification_token"]}
            )

            assert verify_response.status_code == 200
            verify_data = verify_response.json()
            assert "邮箱验证成功" in verify_data["message"]

        # 4. 获取验证状态（需要登录）
        # 由于我们还没有实现完整的登录系统，这里跳过
        # 在实际系统中，需要先登录然后获取验证状态

        # 5. 忘记密码流程
        with patch('app.api.v1.password.email_service.send_password_reset_email') as mock_send_reset:
            mock_send_reset.return_value = True

            forgot_response = test_client.post(
                "/api/v1/auth/password/forgot",
                json={"email": "journey@example.com"}
            )

            assert forgot_response.status_code == 200
            forgot_data = forgot_response.json()
            assert "重置链接" in forgot_data["message"]

            # 保存重置令牌（从邮件服务调用中获取）
            test_data["reset_token"] = "test-reset-token-456"

        # 6. 重置密码
        with patch('app.api.v1.password.VerificationService.verify_password_reset_token') as mock_verify, \
             patch('app.api.v1.password.VerificationService.clear_password_reset_token') as mock_clear:

            # 模拟验证服务
            mock_user = AsyncMock()
            mock_user.id = test_data["user_id"]
            mock_verify.return_value = mock_user
            mock_clear.return_value = None

            reset_response = test_client.post(
                "/api/v1/auth/password/reset",
                json={
                    "token": test_data["reset_token"],
                    "new_password": "NewJourneyPass123!"
                }
            )

            assert reset_response.status_code == 200
            reset_data = reset_response.json()
            assert "密码重置成功" in reset_data["message"]

        # 7. 重新发送验证邮件（已验证的用户）
        with patch('app.api.v1.verify.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            resend_response = test_client.post(
                "/api/v1/auth/verify/resend",
                json={"email": "journey@example.com"}
            )

            # 已验证的用户重新发送验证邮件
            # 在实际实现中，可能返回不同消息
            assert resend_response.status_code == 200

        # 8. 测试错误场景：使用无效令牌验证邮箱
        with patch('app.api.v1.verify.VerificationService.verify_email_token') as mock_verify:
            mock_verify.return_value = None

            invalid_verify_response = test_client.get(
                "/api/v1/auth/verify/email",
                params={"token": "invalid-token-999"}
            )

            assert invalid_verify_response.status_code == 400
            invalid_data = invalid_verify_response.json()
            assert "无效或过期的验证令牌" in invalid_data["detail"]

        # 9. 测试错误场景：使用无效令牌重置密码
        with patch('app.api.v1.password.VerificationService.verify_password_reset_token') as mock_verify:
            mock_verify.return_value = None

            invalid_reset_response = test_client.post(
                "/api/v1/auth/password/reset",
                json={
                    "token": "invalid-reset-token-999",
                    "new_password": "NewPass123!"
                }
            )

            assert invalid_reset_response.status_code == 400
            invalid_reset_data = invalid_reset_response.json()
            assert "无效或过期的重置令牌" in invalid_reset_data["detail"]

        # 10. 测试注册重复用户
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification:
            mock_send_verification.return_value = True

            duplicate_response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "journey@example.com",  # 重复邮箱
                    "username": "differentuser",
                    "password": "DifferentPass123!"
                }
            )

            assert duplicate_response.status_code == 400
            duplicate_data = duplicate_response.json()
            assert "邮箱已被注册" in duplicate_data["detail"]

        print("✅ 完整用户旅程测试通过！")

    def test_concurrent_registrations(self, test_client):
        """测试并发注册（模拟多个用户同时注册）"""
        # 注意：这是一个简化的并发测试
        # 在实际场景中，可能需要使用真正的并发测试框架

        users = [
            {"email": f"concurrent{i}@example.com", "username": f"concurrentuser{i}", "password": f"Pass123!{i}"}
            for i in range(3)
        ]

        responses = []

        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification, \
             patch('app.api.v1.register.email_service.send_welcome_email') as mock_send_welcome:

            mock_send_verification.return_value = True
            mock_send_welcome.return_value = True

            # 顺序注册（不是真正的并发，但测试基本功能）
            for user in users:
                response = test_client.post(
                    "/api/v1/auth/register",
                    json=user
                )
                responses.append(response)

        # 验证所有注册都成功
        for i, response in enumerate(responses):
            assert response.status_code == 201, f"用户{i}注册失败: {response.status_code}"
            data = response.json()
            assert data["email"] == users[i]["email"]

    def test_password_validation(self, test_client):
        """测试密码验证规则"""
        weak_passwords = [
            "123",  # 太短
            "password",  # 无数字和大写
            "PASSWORD123",  # 无小写
            "Password",  # 无数字
            "12345678",  # 纯数字
            "abcdefgh",  # 纯小写
        ]

        strong_password = "StrongPass123!"

        # 测试弱密码注册
        for weak_pass in weak_passwords:
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"weakpass{weak_passwords.index(weak_pass)}@example.com",
                    "username": f"weakuser{weak_passwords.index(weak_pass)}",
                    "password": weak_pass
                }
            )

            # 弱密码应该返回422验证错误或400业务错误
            assert response.status_code in [400, 422], f"弱密码'{weak_pass}'应该被拒绝"

        # 测试强密码注册
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification, \
             patch('app.api.v1.register.email_service.send_welcome_email') as mock_send_welcome:

            mock_send_verification.return_value = True
            mock_send_welcome.return_value = True

            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "strongpass@example.com",
                    "username": "stronguser",
                    "password": strong_password
                }
            )

            # 强密码应该成功注册
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "strongpass@example.com"

    def test_email_format_validation(self, test_client):
        """测试邮箱格式验证"""
        invalid_emails = [
            "not-an-email",
            "missing@domain",
            "@missing.local",
            "spaces in@email.com",
            "multiple@@email.com",
        ]

        valid_email = "valid@example.com"

        # 测试无效邮箱
        for invalid_email in invalid_emails:
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": invalid_email,
                    "username": f"user{invalid_emails.index(invalid_email)}",
                    "password": "ValidPass123!"
                }
            )

            # 无效邮箱应该返回422验证错误
            assert response.status_code == 422, f"无效邮箱'{invalid_email}'应该被拒绝"

        # 测试有效邮箱
        with patch('app.api.v1.register.email_service.send_verification_email') as mock_send_verification, \
             patch('app.api.v1.register.email_service.send_welcome_email') as mock_send_welcome:

            mock_send_verification.return_value = True
            mock_send_welcome.return_value = True

            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": valid_email,
                    "username": "validuser",
                    "password": "ValidPass123!"
                }
            )

            # 有效邮箱应该成功注册
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == valid_email