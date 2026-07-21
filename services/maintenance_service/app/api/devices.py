"""设备和设备状态 HTTP API。"""

from fastapi import APIRouter, Query, status

from ..domain.enums import DeviceLifecycleStatus
from ..schemas.devices import DeviceCreate, DeviceRead, DeviceStatusRead, DeviceUpdate
from .dependencies import MaintenanceServiceDep

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
async def list_devices(
    service: MaintenanceServiceDep,
    status: DeviceLifecycleStatus | None = None,
    model: str | None = None,
    keyword: str | None = None,
    include_archived: bool = False,
) -> list[DeviceRead]:
    """按状态、型号或关键词查询设备。"""

    return await service.list_devices(
        status=status,
        model=model,
        keyword=keyword,
        include_archived=include_archived,
    )


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: int, service: MaintenanceServiceDep) -> DeviceRead:
    """查询设备详情。"""

    return await service.get_device(device_id)


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def create_device(payload: DeviceCreate, service: MaintenanceServiceDep) -> DeviceRead:
    """新增设备。"""

    return await service.create_device(payload)


@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device(
    device_id: int,
    payload: DeviceUpdate,
    service: MaintenanceServiceDep,
) -> DeviceRead:
    """修改设备基本信息。"""

    return await service.update_device(device_id, payload)


@router.delete("/{device_id}", response_model=DeviceRead)
async def archive_device(device_id: int, service: MaintenanceServiceDep) -> DeviceRead:
    """归档设备并保留关联历史。"""

    return await service.archive_device(device_id)


@router.get("/{device_id}/statuses", response_model=list[DeviceStatusRead])
async def list_device_statuses(
    device_id: int,
    service: MaintenanceServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DeviceStatusRead]:
    """查询设备状态历史，默认返回最近 50 条。"""

    return await service.list_device_statuses(device_id, limit=limit)
