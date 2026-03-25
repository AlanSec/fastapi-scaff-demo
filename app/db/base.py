# 导入所有模型，确保SQLModel能够创建所有表
from sqlmodel import SQLModel
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.permission import Permission
