"""刷新令牌模型"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class RefreshTokenBase(SQLModel):
    """刷新令牌基础模型"""

    token: str = Field(index=True, unique=True)
    expires_at: datetime
    is_revoked: bool = Field(default=False)


class RefreshToken(RefreshTokenBase, table=True):
    """刷新令牌数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 关系
    user: "User" = Relationship(back_populates="refresh_tokens")
