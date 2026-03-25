from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user_role import UserRole
    from app.models.permission import RolePermission


class RoleBase(SQLModel):
    """角色基础模型"""

    name: str = Field(index=True)
    description: str | None = None
    is_active: bool = Field(default=True)


class Role(RoleBase, table=True):
    """角色数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 外键
    tenant_id: UUID = Field(foreign_key="tenant.id")

    # 关系
    tenant: "Tenant" = Relationship(back_populates="roles")
    users: list["UserRole"] = Relationship(back_populates="role")  # noqa: F821
    permissions: list["RolePermission"] = Relationship(back_populates="role")  # noqa: F821
