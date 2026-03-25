"""合并权限表迁移和认证表迁移

Revision ID: 9210fba83904
Revises: 2e70f0a8af88_add_tenant_id_to_permission_table, e18eac3510d9
Create Date: 2026-03-25 10:02:04.068322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '9210fba83904'
down_revision: Union[str, None] = ('2e70f0a8af88_add_tenant_id_to_permission_table', 'e18eac3510d9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
