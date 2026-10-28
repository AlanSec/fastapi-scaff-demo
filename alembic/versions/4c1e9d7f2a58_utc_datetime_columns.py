"""utc_datetime_columns

时间列统一为 UTC aware（DateTime(timezone=True)）——实体/模型时间来源已统一为
datetime.now(timezone.utc)，此迁移把列类型同步为带时区类型（PostgreSQL 生效，
SQLite 下为 no-op 重建）。

Revision ID: 4c1e9d7f2a58
Revises: 8f3c2a1b9d4e
Create Date: 2026-08-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c1e9d7f2a58'
down_revision: Union[str, None] = '8f3c2a1b9d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 每张表需要改为 timezone=True 的时间列
_TABLES: dict[str, list[str]] = {
    'permissions': ['created_at', 'updated_at'],
    'tenants': ['created_at', 'updated_at'],
    'roles': ['created_at', 'updated_at'],
    'users': [
        'created_at', 'updated_at',
        'reset_token_expires', 'last_login_at', 'locked_until',
    ],
    'refresh_tokens': ['expires_at', 'created_at', 'updated_at'],
    'user_roles': ['created_at'],
    'role_permissions': ['created_at'],
}


def upgrade() -> None:
    for table, columns in _TABLES.items():
        with op.batch_alter_table(table) as batch_op:
            for column in columns:
                batch_op.alter_column(
                    column,
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=column not in ('created_at', 'updated_at'),
                )


def downgrade() -> None:
    for table, columns in _TABLES.items():
        with op.batch_alter_table(table) as batch_op:
            for column in columns:
                batch_op.alter_column(
                    column,
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(),
                    existing_nullable=column not in ('created_at', 'updated_at'),
                )
