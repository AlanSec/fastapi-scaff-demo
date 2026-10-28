"""drop_user_legacy_columns

删除 UserModel 遗留字段：username（由 email 派生，领域实体无此概念）、
failed_login_attempts / locked_until（旧版数据库限流残留，现由 Redis 限流器承载）。

Revision ID: 9e5b3c8d1f27
Revises: 4c1e9d7f2a58
Create Date: 2026-08-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9e5b3c8d1f27'
down_revision: Union[str, None] = '4c1e9d7f2a58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        # 先删 username 列的索引，否则 batch 重建表后会尝试重建指向已删列的索引
        batch_op.drop_index('ix_users_username')
        batch_op.drop_column('username')
        batch_op.drop_column('failed_login_attempts')
        batch_op.drop_column('locked_until')


def downgrade() -> None:
    import sqlalchemy as sa

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index('ix_users_username', ['username'], unique=False)
