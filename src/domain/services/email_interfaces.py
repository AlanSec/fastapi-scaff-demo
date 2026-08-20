"""邮件发送接口（领域层）"""
from abc import ABC, abstractmethod


class EmailSender(ABC):
    """邮件发送服务接口"""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None:
        pass
