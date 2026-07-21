"""应用级 SQLite 初始化测试。"""

import pytest
from sqlalchemy import inspect

from services.maintenance_service.app.db.init_db import initialize_database
from services.maintenance_service.app.db.session import engine


@pytest.mark.asyncio
async def test_application_database_initialization_is_idempotent() -> None:
    """应用启动初始化可以重复执行，并包含全部阶段一表结构。"""

    await initialize_database()
    async with engine.connect() as connection:
        first_tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )

    await initialize_database()
    async with engine.connect() as connection:
        second_tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )

    assert first_tables == second_tables
    assert "devices" in second_tables
    assert "workflow_steps" in second_tables
