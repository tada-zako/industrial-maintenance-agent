"""Mock 数据幂等初始化测试。"""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.maintenance_service.app.db.models import (
    Base,
    Device,
    DeviceStatus,
    ExternalMaterial,
    Problem,
)
from services.maintenance_service.app.db.seed import seed_mock_data


def create_test_database_path() -> Path:
    """在工作区后端数据目录中创建唯一测试数据库路径。"""

    return (
        Path(__file__).resolve().parents[1]
        / "data"
        / f".test-seed-{uuid4().hex}.db"
    )


async def get_seed_counts(session: AsyncSession) -> dict[str, int]:
    """读取当前 Mock 数据表中的记录数量。"""

    return {
        "devices": int(await session.scalar(select(func.count()).select_from(Device)) or 0),
        "statuses": int(
            await session.scalar(select(func.count()).select_from(DeviceStatus)) or 0
        ),
        "problems": int(await session.scalar(select(func.count()).select_from(Problem)) or 0),
        "materials": int(
            await session.scalar(select(func.count()).select_from(ExternalMaterial)) or 0
        ),
    }


@pytest.mark.asyncio
async def test_mock_seed_is_idempotent_and_covers_demo_faults() -> None:
    """重复初始化不增加重复数据，并覆盖三类演示故障。"""

    database_file = create_test_database_path()
    database_file.parent.mkdir(parents=True, exist_ok=True)
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            first_summary = await seed_mock_data(session)
            first_counts = await get_seed_counts(session)
            await session.commit()

            second_summary = await seed_mock_data(session)
            second_counts = await get_seed_counts(session)

            symptoms = set(
                await session.scalars(
                    select(Problem.symptom).where(Problem.status != "archived")
                )
            )
    finally:
        await test_engine.dispose()
        database_file.unlink(missing_ok=True)

    assert first_summary == second_summary
    assert first_counts == second_counts
    assert first_counts == {"devices": 6, "statuses": 6, "problems": 9, "materials": 8}
    assert {"排气压力异常", "温度过高", "振动异常"}.issubset(symptoms)
