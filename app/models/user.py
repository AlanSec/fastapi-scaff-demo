from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user_role import UserRole
    from app.models.refresh_token import RefreshToken


class UserBase(SQLModel):
    """用户基础模型"""

    email: str = Field(index=True, unique=True)
    username: str = Field(index=True)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class User(UserBase, table=True):
    """用户数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 验证字段
    email_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None, nullable=True)
    reset_token: Optional[str] = Field(default=None, nullable=True)
    reset_token_expires: Optional[datetime] = Field(default=None, nullable=True)

    # 登录限制字段
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None, nullable=True)

    # 外键
    tenant_id: UUID = Field(foreign_key="tenant.id")

    # 关系
    tenant: "Tenant" = Relationship(back_populates="users")
    roles: list["UserRole"] = Relationship(back_populates="user")  # noqa: F821
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")
