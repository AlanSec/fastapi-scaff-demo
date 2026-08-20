"""控制台邮件发送器——将邮件内容写入日志（无真实 SMTP 时的安全降级实现）"""
import logging

from src.domain.services.email_interfaces import EmailSender

logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSender):
    """把邮件输出到日志而非真正发送。

    - 不向 API 调用方泄露 token（避免之前 token 直接出现在响应体的问题）
    - 生产环境接入真实 SMTP 时，替换为 SMTPEmailSender 即可
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%s\n%s", to, subject, body)
