from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True
    tenant_id: Optional[UUID] = None


class PermissionCreate(PermissionBase):
    """创建权限模型"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限模型"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    tenant_id: Optional[UUID] = None


class PermissionOut(PermissionBase):
    """权限输出模型"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
