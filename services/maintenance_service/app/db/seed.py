"""SQLite 表结构和 AI Mock 业务数据的幂等初始化。"""

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.seed import MockDeviceRecord, MockMaterialRecord, MockProblemRecord, MockStatusRecord
from .init_db import initialize_database
from .repositories import (
    DeviceRepository,
    DeviceStatusRepository,
    MaterialRepository,
    ProblemRepository,
)
from .session import session_context

DEFAULT_MOCK_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "mock"


@dataclass(frozen=True, slots=True)
class SeedSummary:
    """一次 Mock 初始化处理的记录数量摘要。"""

    devices: int
    statuses: int
    problems: int
    materials: int


def _load_records[T](path: Path, adapter: TypeAdapter[T]) -> list[T]:
    """读取 JSON 并使用 Pydantic 校验 Mock 数据文件。"""

    if not path.is_file():
        raise FileNotFoundError(f"Mock 数据文件不存在: {path}")
    return adapter.validate_json(path.read_text(encoding="utf-8"))


async def seed_mock_data(
    session: AsyncSession,
    *,
    data_dir: Path = DEFAULT_MOCK_DATA_DIR,
) -> SeedSummary:
    """在一个明确事务内幂等写入 Mock 设备、状态、问题和资料。"""

    devices = _load_records(
        data_dir / "devices.json", TypeAdapter(list[MockDeviceRecord])
    )
    statuses = _load_records(
        data_dir / "device_statuses.json", TypeAdapter(list[MockStatusRecord])
    )
    problems = _load_records(
        data_dir / "problems.json", TypeAdapter(list[MockProblemRecord])
    )
    materials = _load_records(
        data_dir / "materials.json", TypeAdapter(list[MockMaterialRecord])
    )

    device_repository = DeviceRepository(session)
    status_repository = DeviceStatusRepository(session)
    problem_repository = ProblemRepository(session)
    material_repository = MaterialRepository(session)

    async with session.begin():
        device_ids: dict[str, int] = {}
        for record in devices:
            device = await device_repository.upsert_seed_record(
                record.model_dump(mode="python")
            )
            device_ids[record.code] = device.id

        for record in statuses:
            device_id = device_ids.get(record.device_code)
            if device_id is None:
                raise ValueError(f"状态引用了未知设备: {record.device_code}")
            payload = record.model_dump(mode="python")
            payload.pop("device_code")
            await status_repository.upsert_seed_record(
                device_id=device_id,
                collected_at=record.collected_at,
                source=record.source,
                values=payload,
            )

        for record in problems:
            device_id = device_ids.get(record.device_code)
            if device_id is None:
                raise ValueError(f"问题引用了未知设备: {record.device_code}")
            payload = record.model_dump(mode="python")
            payload.pop("device_code")
            await problem_repository.upsert_seed_record(
                device_id=device_id,
                symptom=record.symptom,
                detected_at=record.detected_at,
                values=payload,
            )

        for record in materials:
            payload = record.model_dump(mode="python")
            await material_repository.upsert_seed_record(
                filename=record.filename,
                source_description=record.source_description,
                values=payload,
            )

    return SeedSummary(
        devices=len(devices),
        statuses=len(statuses),
        problems=len(problems),
        materials=len(materials),
    )


async def initialize_mock_data(*, data_dir: Path = DEFAULT_MOCK_DATA_DIR) -> SeedSummary:
    """初始化表结构并写入默认 Mock 数据，供本地命令和 Compose 使用。"""

    await initialize_database()
    async with session_context() as session:
        return await seed_mock_data(session, data_dir=data_dir)


async def _main() -> None:
    summary = await initialize_mock_data()
    print(json.dumps(asdict(summary), ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(_main())
