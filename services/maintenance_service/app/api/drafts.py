"""维修草案 HTTP API。草案始终需要人工确认。"""

from fastapi import APIRouter, status

from ..domain.enums import DraftStatus
from ..schemas.drafts import (
    MaintenanceDraftCreate,
    MaintenanceDraftRead,
    MaintenanceDraftStatusUpdate,
)
from .dependencies import MaintenanceServiceDep

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.get("", response_model=list[MaintenanceDraftRead])
async def list_drafts(
    service: MaintenanceServiceDep,
    device_id: int | None = None,
    status: DraftStatus | None = None,
    include_archived: bool = False,
) -> list[MaintenanceDraftRead]:
    """按设备或状态查询维修草案。"""

    return await service.list_drafts(
        device_id=device_id, status=status, include_archived=include_archived
    )


@router.get("/{draft_id}", response_model=MaintenanceDraftRead)
async def get_draft(draft_id: int, service: MaintenanceServiceDep) -> MaintenanceDraftRead:
    """获取草案详情和证据引用。"""

    return await service.get_draft(draft_id)


@router.post("", response_model=MaintenanceDraftRead, status_code=status.HTTP_201_CREATED)
async def create_draft(
    payload: MaintenanceDraftCreate, service: MaintenanceServiceDep
) -> MaintenanceDraftRead:
    """保存结构化草案，供 MCP 和演示接口复用。"""

    return await service.create_draft(payload)


@router.patch("/{draft_id}/status", response_model=MaintenanceDraftRead)
async def update_draft_status(
    draft_id: int,
    payload: MaintenanceDraftStatusUpdate,
    service: MaintenanceServiceDep,
) -> MaintenanceDraftRead:
    """仅允许修改草案状态与人工确认标记。"""

    return await service.update_draft_status(
        draft_id,
        status=payload.status,
        requires_human_confirmation=payload.requires_human_confirmation,
        review_feedback=payload.review_feedback,
    )


@router.delete("/{draft_id}", response_model=MaintenanceDraftRead)
async def archive_draft(draft_id: int, service: MaintenanceServiceDep) -> MaintenanceDraftRead:
    """归档草案而不物理删除其历史。"""

    return await service.archive_draft(draft_id)
