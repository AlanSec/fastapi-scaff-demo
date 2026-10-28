"""SQLModel 数据模型"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from src.infrastructure.persistence.sqlmodel.models.time import utcnow

if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.refresh_token import RefreshTokenModel
    from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel
    from src.infrastructure.persistence.sqlmodel.models.user_role import UserRoleModel


class UserModel(SQLModel, table=True):
    """用户数据模型"""
    __tablename__ = "users"
    # 邮箱按租户唯一：同一邮箱可注册到不同租户（与领域层语义一致）
    __table_args__ = (
        UniqueConstraint("email", "tenant_id", name="uq_users_email_tenant"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    email_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None, nullable=True)
    reset_token: Optional[str] = Field(default=None, nullable=True)
    reset_token_expires: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)

    tenant: "TenantModel" = Relationship(back_populates="users")
    roles: list["UserRoleModel"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    refresh_tokens: list["RefreshTokenModel"] = Relationship(
        back_populates="user", cascade_delete=True
    )
