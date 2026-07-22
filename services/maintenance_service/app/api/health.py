"""服务健康检查接口。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """返回进程级健康状态；外部数据库连通性检查后续单独扩展。"""

    return {"status": "ok", "service": "maintenance-service"}
