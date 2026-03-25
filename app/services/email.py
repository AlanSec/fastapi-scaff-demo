import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""

    def __init__(self):
        self.smtp_host = getattr(settings, 'SMTP_HOST', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.smtp_from = getattr(settings, 'SMTP_FROM', 'noreply@example.com')
        self.use_tls = getattr(settings, 'SMTP_USE_TLS', True)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）

        Returns:
            bool: 发送是否成功
        """
        try:
            # 在线程池中运行同步的SMTP操作
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._send_sync_email,
                to_email,
                subject,
                html_content,
                text_content
            )
            return success
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    def _send_sync_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """同步发送邮件（在线程池中运行）"""
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email

            # 添加纯文本部分
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

            # 添加HTML部分
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"邮件发送成功: {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP发送失败: {e}")
            return False

    async def send_verification_email(self, to_email: str, verification_token: str, username: str) -> bool:
        """发送邮箱验证邮件

        Args:
            to_email: 收件人邮箱
            verification_token: 验证令牌
            username: 用户名

        Returns:
            bool: 发送是否成功
        """
        # TODO: 从配置中获取前端URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email?token={verification_token}"

        subject = "请验证您的邮箱"
        html_content = f"""
        <html>
        <body>
            <h2>欢迎 {username}！</h2>
            <p>感谢您注册我们的服务。请点击以下链接验证您的邮箱：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>如果链接无法点击，请复制以上链接到浏览器地址栏访问。</p>
            <p>此链接24小时内有效。</p>
            <br/>
            <p>如果您没有注册，请忽略此邮件。</p>
        </body>
        </html>
        """

        text_content = f"""
        欢迎 {username}！

        感谢您注册我们的服务。请访问以下链接验证您的邮箱：
        {verification_url}

        此链接24小时内有效。

        如果您没有注册，请忽略此邮件。
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """发送密码重置邮件

        Args:
            to_email: 收件人邮箱
            reset_token: 重置令牌
            username: 用户名

        Returns:
            bool: 发送是否成功
        """
        # TODO: 从配置中获取前端URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        subject = "重置您的密码"
        html_content = f"""
        <html>
        <body>
            <h2>密码重置请求</h2>
            <p>尊敬的 {username}，</p>
            <p>我们收到了您的密码重置请求。请点击以下链接重置您的密码：</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>如果链接无法点击，请复制以上链接到浏览器地址栏访问。</p>
            <p>此链接1小时内有效。</p>
            <br/>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
        </body>
        </html>
        """

        text_content = f"""
        密码重置请求

        尊敬的 {username}，

        我们收到了您的密码重置请求。请访问以下链接重置您的密码：
        {reset_url}

        此链接1小时内有效。

        如果您没有请求重置密码，请忽略此邮件。
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_welcome_email(self, to_email: str, username: str) -> bool:
        """发送欢迎邮件

        Args:
            to_email: 收件人邮箱
            username: 用户名

        Returns:
            bool: 发送是否成功
        """
        subject = "欢迎加入我们！"
        html_content = f"""
        <html>
        <body>
            <h2>欢迎 {username}！</h2>
            <p>感谢您注册我们的服务。您的账户已创建成功。</p>
            <p>请尽情探索我们的功能吧！</p>
            <br/>
            <p>如果您有任何问题，请随时联系我们。</p>
        </body>
        </html>
        """

        text_content = f"""
        欢迎 {username}！

        感谢您注册我们的服务。您的账户已创建成功。

        请尽情探索我们的功能吧！

        如果您有任何问题，请随时联系我们。
        """

        return await self.send_email(to_email, subject, html_content, text_content)


# 全局邮件服务实例
email_service = EmailService()