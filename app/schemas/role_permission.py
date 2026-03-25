from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RolePermissionBase(BaseModel):
    """角色权限关联基础模型"""
    role_id: UUID
    permission_id: UUID
    is_active: bool = True


class RolePermissionCreate(RolePermissionBase):
    """创建角色权限关联模型"""
    pass


class RolePermissionOut(RolePermissionBase):
    """角色权限关联输出模型"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
