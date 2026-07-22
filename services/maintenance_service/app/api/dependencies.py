"""FastAPI 请求依赖，统一创建 Session 和共享业务服务。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..domain.services import MaintenanceService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_maintenance_service(session: SessionDep) -> MaintenanceService:
    """为每个请求绑定一个使用当前 AsyncSession 的业务服务。"""

    return MaintenanceService(session)


MaintenanceServiceDep = Annotated[
    MaintenanceService,
    Depends(get_maintenance_service),
]
