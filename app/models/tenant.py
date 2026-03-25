from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.user import User


class TenantBase(SQLModel):
    """租户基础模型"""

    name: str = Field(index=True)
    description: str | None = None
    is_active: bool = Field(default=True)


class Tenant(TenantBase, table=True):
    """租户数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 关系
    users: list["User"] = Relationship(back_populates="tenant")  # noqa: F821
    roles: list["Role"] = Relationship(back_populates="tenant")  # noqa: F821
