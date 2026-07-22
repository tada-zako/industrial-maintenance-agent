"""SQLite 建表入口；MVP 阶段使用 SQLAlchemy metadata 初始化，不引入迁移系统。"""

from pathlib import Path

from ..config import settings
from .models import Base
from .session import engine


def _ensure_sqlite_parent_dir() -> None:
    """为文件型 SQLite 创建父目录，内存数据库不需要目录。"""

    if not settings.database_url.startswith("sqlite"):
        return
    database_part = settings.database_url.split("///", maxsplit=1)[-1].split("?", maxsplit=1)[0]
    if database_part == ":memory:":
        return
    Path(database_part).expanduser().parent.mkdir(parents=True, exist_ok=True)


async def initialize_database() -> None:
    """创建表并为已存在的本地 Demo 数据补齐小范围兼容字段。"""

    _ensure_sqlite_parent_dir()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if connection.dialect.name == "sqlite":
            result = await connection.exec_driver_sql("PRAGMA table_info(maintenance_drafts)")
            columns = {row[1] for row in result.fetchall()}
            # MVP 未使用迁移框架；仅为已有本地演示库补充两个可空审核字段。
            if "review_feedback" not in columns:
                await connection.exec_driver_sql(
                    "ALTER TABLE maintenance_drafts ADD COLUMN review_feedback TEXT"
                )
            if "reviewed_at" not in columns:
                await connection.exec_driver_sql(
                    "ALTER TABLE maintenance_drafts ADD COLUMN reviewed_at DATETIME"
                )
