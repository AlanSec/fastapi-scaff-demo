from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class RolePermissionBase(SQLModel):
    """角色-权限关联基础模型"""

    is_active: bool = Field(default=True)


class RolePermission(RolePermissionBase, table=True):
    """角色-权限关联数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 外键
    role_id: UUID = Field(foreign_key="role.id")
    permission_id: UUID = Field(foreign_key="permission.id")

    # 关系
    role: "Role" = Relationship(back_populates="permissions")  # noqa: F821
    permission: "Permission" = Relationship(back_populates="roles")  # noqa: F821
