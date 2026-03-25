"""添加角色权限认证相关表

Revision ID: 20250307_001_add_auth_tables
Revises: b8d747f7ff6d
Create Date: 2025-03-07 10:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20250307_001_add_auth_tables'
down_revision: Union[str, None] = 'b8d747f7ff6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### 删除可能已存在的表（如果结构不匹配） ###
    # 按依赖顺序删除：先删除关联表，再删除主表
    # 使用原始SQL以支持CASCADE
    op.execute('DROP TABLE IF EXISTS role_permission CASCADE;')
    op.execute('DROP TABLE IF EXISTS rolepermission CASCADE;')
    op.execute('DROP TABLE IF EXISTS user_role CASCADE;')
    op.execute('DROP TABLE IF EXISTS permission CASCADE;')
    op.execute('DROP TABLE IF EXISTS role CASCADE;')

    # ### 创建角色表 ###
    op.create_table('role',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=False)

    # ### 创建权限表 ###
    op.create_table('permission',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('parent_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['permission.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_name'), 'permission', ['name'], unique=False)
    op.create_index(op.f('ix_permission_code'), 'permission', ['code'], unique=True)

    # ### 创建用户-角色关联表 ###
    op.create_table('user_role',
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_role_user_id_role_id', 'user_role', ['user_id', 'role_id'], unique=True)

    # ### 创建角色-权限关联表 ###
    op.create_table('role_permission',
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('permission_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_role_permission_role_id_permission_id', 'role_permission', ['role_id', 'permission_id'], unique=True)

    # ### 为用户表添加验证字段 ###
    # 先删除可能已存在的字段
    op.drop_column('user', 'email_verified', if_exists=True)
    op.drop_column('user', 'verification_token', if_exists=True)
    op.drop_column('user', 'reset_token', if_exists=True)
    op.drop_column('user', 'reset_token_expires', if_exists=True)
    # 添加字段
    op.add_column('user', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user', sa.Column('verification_token', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('reset_token', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))

    # ### 插入默认数据 ###
    # 注意：这里需要先有tenant记录，如果不存在则创建默认tenant
    conn = op.get_bind()

    # 检查tenant是否存在
    result = conn.execute(sa.text("SELECT id, name FROM tenant LIMIT 1"))
    tenant_row = result.fetchone()

    if tenant_row:
        tenant_id = tenant_row[0]
        tenant_name = tenant_row[1]
        print(f"使用现有tenant: {tenant_name} (ID: {tenant_id})")
    else:
        # 创建默认tenant
        default_tenant_id = str(uuid4())
        default_tenant_name = "默认租户"
        print(f"创建默认tenant: {default_tenant_name} (ID: {default_tenant_id})")

        op.bulk_insert(
            sa.table('tenant',
                sa.Column('id', sa.Uuid()),
                sa.Column('name', sqlmodel.sql.sqltypes.AutoString()),
                sa.Column('description', sqlmodel.sql.sqltypes.AutoString()),
                sa.Column('is_active', sa.Boolean()),
                sa.Column('created_at', sa.DateTime()),
                sa.Column('updated_at', sa.DateTime())
            ),
            [
                {
                    'id': default_tenant_id,
                    'name': default_tenant_name,
                    'description': '系统默认租户',
                    'is_active': True,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            ]
        )
        tenant_id = default_tenant_id

    # 插入默认角色
    admin_role_id = str(uuid4())
    user_role_id = str(uuid4())

    op.bulk_insert(
        sa.table('role',
            sa.Column('id', sa.Uuid()),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString()),
            sa.Column('description', sqlmodel.sql.sqltypes.AutoString()),
            sa.Column('is_active', sa.Boolean()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
            sa.Column('tenant_id', sa.Uuid())
        ),
        [
            {
                'id': admin_role_id,
                'name': 'admin',
                'description': '系统管理员，拥有所有权限',
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'tenant_id': tenant_id
            },
            {
                'id': user_role_id,
                'name': 'user',
                'description': '普通用户',
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'tenant_id': tenant_id
            }
        ]
    )

    # 插入默认权限（基础CRUD权限）
    permissions = [
        {
            'id': str(uuid4()),
            'name': '用户管理-查看',
            'code': 'user:read',
            'description': '查看用户信息',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '用户管理-创建',
            'code': 'user:create',
            'description': '创建新用户',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '用户管理-更新',
            'code': 'user:update',
            'description': '更新用户信息',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '用户管理-删除',
            'code': 'user:delete',
            'description': '删除用户',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '角色管理-查看',
            'code': 'role:read',
            'description': '查看角色信息',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '角色管理-创建',
            'code': 'role:create',
            'description': '创建新角色',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '角色管理-更新',
            'code': 'role:update',
            'description': '更新角色信息',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '角色管理-删除',
            'code': 'role:delete',
            'description': '删除角色',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '权限管理-查看',
            'code': 'permission:read',
            'description': '查看权限信息',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '权限管理-创建',
            'code': 'permission:create',
            'description': '创建新权限',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '权限管理-更新',
            'code': 'permission:update',
            'description': '更新权限信息',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        },
        {
            'id': str(uuid4()),
            'name': '权限管理-删除',
            'code': 'permission:delete',
            'description': '删除权限',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    ]

    # 批量插入权限
    op.bulk_insert(
        sa.table('permission',
            sa.Column('id', sa.Uuid()),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString()),
            sa.Column('code', sqlmodel.sql.sqltypes.AutoString()),
            sa.Column('description', sqlmodel.sql.sqltypes.AutoString()),
            sa.Column('is_active', sa.Boolean()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
            sa.Column('parent_id', sa.Uuid())
        ),
        permissions
    )

    # 为admin角色分配所有权限
    role_permissions = []
    for permission in permissions:
        role_permissions.append({
            'id': str(uuid4()),
            'role_id': admin_role_id,
            'permission_id': permission['id'],
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })

    op.bulk_insert(
        sa.table('role_permission',
            sa.Column('id', sa.Uuid()),
            sa.Column('role_id', sa.Uuid()),
            sa.Column('permission_id', sa.Uuid()),
            sa.Column('is_active', sa.Boolean()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime())
        ),
        role_permissions
    )

    print("默认角色权限数据插入完成")


def downgrade() -> None:
    """Downgrade schema."""
    # ### 删除用户表验证字段 ###
    op.drop_column('user', 'reset_token_expires')
    op.drop_column('user', 'reset_token')
    op.drop_column('user', 'verification_token')
    op.drop_column('user', 'email_verified')

    # ### 删除关联表 ###
    op.drop_table('role_permission')
    op.drop_table('user_role')

    # ### 删除主表 ###
    op.drop_index(op.f('ix_permission_code'), table_name='permission')
    op.drop_index(op.f('ix_permission_name'), table_name='permission')
    op.drop_table('permission')

    op.drop_index(op.f('ix_role_name'), table_name='role')
    op.drop_table('role')