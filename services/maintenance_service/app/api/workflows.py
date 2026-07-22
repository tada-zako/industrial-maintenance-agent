"""Agent 工作流查询 API。"""

from fastapi import APIRouter

from ..schemas.workflows import WorkflowRunRead
from .dependencies import MaintenanceServiceDep

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/{run_id}", response_model=WorkflowRunRead)
async def get_workflow(run_id: int, service: MaintenanceServiceDep) -> WorkflowRunRead:
    """查询一次工作流和已记录的工具调用步骤。"""

    return await service.get_workflow(run_id)
