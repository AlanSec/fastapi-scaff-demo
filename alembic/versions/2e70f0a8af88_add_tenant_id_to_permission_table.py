"""add tenant_id to permission

Revision ID: <会自动生成>
Revises: <前一个版本号>
Create Date: <当前日期>

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2e70f0a8af88_add_tenant_id_to_permission_table'
down_revision: Union[str, None] = 'b8d747f7ff6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 tenant_id 字段"""
    # 添加 tenant_id 列，允许 NULL（因为已有数据）
    op.add_column('permission', sa.Column('tenant_id', sa.UUID(), nullable=True))

    # 如果需要，可以为现有记录设置默认值
    # op.execute("UPDATE permission SET tenant_id = (SELECT id FROM tenant LIMIT 1)")

    # 添加外键约束
    op.create_foreign_key(
        'fk_permission_tenant',
        'permission',
        'tenant',
        ['tenant_id'],
        ['id']
    )


def downgrade() -> None:
    """回滚迁移"""
    op.drop_constraint('fk_permission_tenant', 'permission', type_='foreignkey')
    op.drop_column('permission', 'tenant_id')
