"""问题和历史故障 HTTP API。"""

from fastapi import APIRouter, status

from ..domain.enums import ProblemSeverity, ProblemStatus
from ..schemas.problems import ProblemCreate, ProblemRead, ProblemUpdate
from .dependencies import MaintenanceServiceDep

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemRead])
async def list_problems(
    service: MaintenanceServiceDep,
    device_id: int | None = None,
    symptom: str | None = None,
    severity: ProblemSeverity | None = None,
    status: ProblemStatus | None = None,
    keyword: str | None = None,
    include_archived: bool = False,
) -> list[ProblemRead]:
    """按设备、现象、严重程度、状态或关键词查询问题。"""

    return await service.list_problems(
        device_id=device_id,
        symptom=symptom,
        severity=severity,
        status=status,
        keyword=keyword,
        include_archived=include_archived,
    )


@router.get("/{problem_id}", response_model=ProblemRead)
async def get_problem(problem_id: int, service: MaintenanceServiceDep) -> ProblemRead:
    """查询问题详情。"""

    return await service.get_problem(problem_id)


@router.post("", response_model=ProblemRead, status_code=status.HTTP_201_CREATED)
async def create_problem(payload: ProblemCreate, service: MaintenanceServiceDep) -> ProblemRead:
    """新增问题。"""

    return await service.create_problem(payload)


@router.patch("/{problem_id}", response_model=ProblemRead)
async def update_problem(
    problem_id: int,
    payload: ProblemUpdate,
    service: MaintenanceServiceDep,
) -> ProblemRead:
    """修改问题描述、严重程度或处理状态。"""

    return await service.update_problem(problem_id, payload)


@router.delete("/{problem_id}", response_model=ProblemRead)
async def archive_problem(problem_id: int, service: MaintenanceServiceDep) -> ProblemRead:
    """归档问题并保留历史记录。"""

    return await service.archive_problem(problem_id)
