# 导入项目配置和模型
import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from pathlib import Path
load_dotenv()

# BASE_DIR = Path(__file__).resolve()
# os.chdir(BASE_DIR)  # 确保从项目根目录加载.env
# # 加载环境变量
# load_dotenv(BASE_DIR / ".env")
# print(f"当前工作目录: {os.getcwd()}")
# print(f"正在从 {BASE_DIR / '.env'} 加载配置")
# print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")

# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.core.config import settings
from app.db.base import SQLModel


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 从应用配置中获取数据库 URL
# 将 asyncpg 替换为 psycopg2，因为 Alembic 使用同步连接
db_url = str(settings.SQLALCHEMY_DATABASE_URI)
db_url = db_url.replace("+asyncpg", "+psycopg2")
print(f"数据库连接 URL: {db_url}")
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

# 导入所有模型，确保它们被注册到元数据中
from app.models import tenant, user, role, user_role, role_permission, permission, refresh_token  # noqa

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
