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

from sqlmodel import SQLModel  # noqa: E402
import src.infrastructure.persistence.sqlmodel.models  # noqa: E402, F401

conn = sqlite3.connect(DB_PATH)
tables = sorted(
    r[0]
    for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'alembic_%'"
    )
)
conn.close()
DB_PATH.unlink()

print("alembic 建的表:", tables)
print("SQLModel 模型表:", sorted(SQLModel.metadata.tables.keys()))
assert tables == sorted(SQLModel.metadata.tables.keys()), "MISMATCH"
print("ALEMBIC BASELINE 与模型一致 OK")
