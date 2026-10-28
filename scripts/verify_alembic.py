"""验证 alembic baseline 迁移与 SQLModel 模型一致（自包含：先对临时库执行 upgrade head）"""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "alembic_tmp.db"

if DB_PATH.exists():
    DB_PATH.unlink()

# 用临时 SQLite 库执行全部迁移（继承 stdio，避免管道限制）
env = dict(os.environ, DATABASE_URL=f"sqlite:///{DB_PATH.as_posix()}")
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=str(ROOT),
    env=env,
    check=True,
)

sys.path.insert(0, str(ROOT))

import src.infrastructure.persistence.sqlmodel.models  # noqa: E402, F401
from sqlmodel import SQLModel  # noqa: E402

conn = sqlite3.connect(DB_PATH)
tables = sorted(
    r[0]
    for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'alembic_%'"
    )
)


def unique_column_sets(table: str) -> set[frozenset]:
    """返回表中全部唯一索引/约束的列集合（SQLite 的命名唯一约束会变成 sqlite_autoindex_N）"""
    result = set()
    for row in conn.execute(f"PRAGMA index_list({table})"):
        name, unique = row[1], row[2]
        if unique:
            cols = frozenset(r[2] for r in conn.execute(f"PRAGMA index_info({name})"))
            result.add(cols)
    return result


# 租户隔离的数据库层支撑：组合唯一约束（按列集合断言，兼容 SQLite autoindex）
assert frozenset({"email", "tenant_id"}) in unique_column_sets("users"), (
    "users 缺少 (email, tenant_id) 唯一约束"
)
assert frozenset({"user_id", "role_id"}) in unique_column_sets("user_roles"), (
    "user_roles 缺少唯一约束"
)
assert frozenset({"role_id", "permission_id"}) in unique_column_sets("role_permissions"), (
    "role_permissions 缺少唯一约束"
)

# email 全局唯一索引应已移除（改为组合唯一）
assert frozenset({"email"}) not in unique_column_sets("users"), "email 全局唯一索引应已被移除"

conn.close()
DB_PATH.unlink()

print("alembic 建的表:", tables)
print("SQLModel 模型表:", sorted(SQLModel.metadata.tables.keys()))
assert tables == sorted(SQLModel.metadata.tables.keys()), "MISMATCH"
print("ALEMBIC 迁移与模型一致 OK（含租户隔离约束）")
