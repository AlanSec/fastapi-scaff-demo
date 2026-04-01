"""SQLModel 数据模型"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel
    from src.infrastructure.persistence.sqlmodel.models.user_role import UserRoleModel
    from src.infrastructure.persistence.sqlmodel.models.refresh_token import RefreshTokenModel


class UserModel(SQLModel, table=True):
    """用户数据模型"""
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    email_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None, nullable=True)
    reset_token: Optional[str] = Field(default=None, nullable=True)
    reset_token_expires: Optional[datetime] = Field(default=None, nullable=True)
    
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None, nullable=True)
    
    tenant_id: UUID = Field(foreign_key="tenants.id")
    
    tenant: "TenantModel" = Relationship(back_populates="users")
    roles: list["UserRoleModel"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshTokenModel"] = Relationship(back_populates="user")