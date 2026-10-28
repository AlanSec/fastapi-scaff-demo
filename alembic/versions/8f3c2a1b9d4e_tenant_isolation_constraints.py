"""tenant_isolation_constraints

邮箱按租户唯一 + 关联表唯一约束与索引（租户隔离的数据库层支撑）

Revision ID: 8f3c2a1b9d4e
Revises: 742419bf3b87
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f3c2a1b9d4e'
down_revision: Union[str, None] = '742419bf3b87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users：email 全局唯一 → (email, tenant_id) 组合唯一 ---
    # 前提：现有数据中同一 email 不能出现在多个租户（脚手架阶段默认满足；
    # 若存在重复需先手工去重，否则 SQLite 重建表时会因唯一约束失败）。
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_email')
        batch_op.create_index('ix_users_tenant_id', ['tenant_id'], unique=False)
        batch_op.create_unique_constraint('uq_users_email_tenant', ['email', 'tenant_id'])

    # --- user_roles：同一用户不可重复分配同一角色 + role_id 索引 ---
    with op.batch_alter_table('user_roles') as batch_op:
        batch_op.create_index('ix_user_roles_role_id', ['role_id'], unique=False)
        batch_op.create_unique_constraint('uq_user_roles_user_role', ['user_id', 'role_id'])

    # --- role_permissions：同一角色不可重复关联同一权限 + permission_id 索引 ---
    with op.batch_alter_table('role_permissions') as batch_op:
        batch_op.create_index('ix_role_permissions_permission_id', ['permission_id'], unique=False)
        batch_op.create_unique_constraint('uq_role_permissions_role_perm', ['role_id', 'permission_id'])

    # --- refresh_tokens：user_id 索引（按用户查询/级联） ---
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.create_index('ix_refresh_tokens_user_id', ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.drop_index('ix_refresh_tokens_user_id')

    with op.batch_alter_table('role_permissions') as batch_op:
        batch_op.drop_constraint('uq_role_permissions_role_perm', type_='unique')
        batch_op.drop_index('ix_role_permissions_permission_id')

    with op.batch_alter_table('user_roles') as batch_op:
        batch_op.drop_constraint('uq_user_roles_user_role', type_='unique')
        batch_op.drop_index('ix_user_roles_role_id')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('uq_users_email_tenant', type_='unique')
        batch_op.drop_index('ix_users_tenant_id')
        batch_op.create_index('ix_users_email', ['email'], unique=True)
