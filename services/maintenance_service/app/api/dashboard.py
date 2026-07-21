"""运维看板统计 API。"""

from fastapi import APIRouter

from ..schemas.dashboard import DashboardSummaryRead
from .dependencies import MaintenanceServiceDep

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryRead)
async def get_dashboard_summary(service: MaintenanceServiceDep) -> DashboardSummaryRead:
    """返回演示看板的基础计数和最近工作流编号。"""

    return await service.dashboard_summary()
