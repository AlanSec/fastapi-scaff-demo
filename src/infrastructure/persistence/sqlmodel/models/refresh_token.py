"""刷新令牌 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.user import UserModel


class RefreshTokenModel(SQLModel, table=True):
    """刷新令牌数据模型"""
    __tablename__ = "refresh_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    token: str = Field(index=True, unique=True)
    user_id: UUID = Field(foreign_key="users.id")
    expires_at: datetime
    is_revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    user: "UserModel" = Relationship(back_populates="refresh_tokens")