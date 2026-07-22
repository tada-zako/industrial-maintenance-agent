"""受控的知识图谱只读 HTTP API。"""

from fastapi import APIRouter, Query

from ..graph.queries import KnowledgeGraphService
from ..schemas.knowledge import KnowledgePathResult, KnowledgeRelatedResult

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/related")
async def get_related_knowledge(
    keyword: str = "",
    device_model: str | None = None,
    device_code: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> KnowledgeRelatedResult:
    """按关键词返回整理后的图谱证据，不暴露 Cypher 或连接信息。"""

    return await KnowledgeGraphService().search(
        keyword=keyword, device_model=device_model, device_code=device_code, limit=limit
    )


@router.get("/path")
async def get_knowledge_path(
    symptom: str,
    limit: int = Query(default=10, ge=1, le=20),
) -> list[KnowledgePathResult]:
    """返回一个故障现象到维修措施的证据路径。"""

    return await KnowledgeGraphService().path(symptom=symptom, limit=limit)
