"""Neo4j 知识图谱的参数化查询服务。"""

from typing import Any

from neo4j import AsyncDriver

from .client import GraphUnavailableError, graph_driver


class KnowledgeGraphService:
    """整理节点、关系和证据链，供 API 与 MCP 共同使用。"""

    async def _query(self, cypher: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        async with graph_driver() as driver:
            return await self._query_with_driver(driver, cypher, parameters)

    async def _query_with_driver(
        self, driver: AsyncDriver, cypher: str, parameters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        async with driver.session() as session:
            result = await session.run(cypher, parameters)
            return [record.data() async for record in result]

    async def search(
        self,
        *,
        keyword: str = "",
        device_model: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """按故障现象或关键词返回原因、措施、SOP 和安全事项。"""

        normalized_keyword = keyword.strip()
        rows = await self._query(
            """
            MATCH (symptom:FaultSymptom)
            WHERE $keyword = '' OR toLower(symptom.name) CONTAINS toLower($keyword)
            OPTIONAL MATCH (symptom)-[:MAY_BE_CAUSED_BY]->(cause:FaultCause)
            OPTIONAL MATCH (cause)-[:SOLVED_BY]->(action:MaintenanceAction)
            OPTIONAL MATCH (action)-[:REFER_TO]->(sop:SOP)
            OPTIONAL MATCH (action)-[:REQUIRES]->(notice:SafetyNotice)
            RETURN symptom.name AS symptom,
                   collect(DISTINCT cause.name) AS causes,
                   collect(DISTINCT action.name) AS actions,
                   collect(DISTINCT sop.name) AS sops,
                   collect(DISTINCT notice.name) AS safety_notices
            ORDER BY symptom
            LIMIT $limit
            """,
            {"keyword": normalized_keyword, "limit": limit},
        )
        cases = await self._query(
            """
            MATCH (case:MaintenanceCase)-[:APPLIES_TO]->(model:DeviceModel)
            OPTIONAL MATCH (case)-[:ADDRESSES]->(symptom:FaultSymptom)
            WHERE $device_model IS NULL OR model.name = $device_model
            RETURN case.name AS name, model.name AS device_model,
                   collect(DISTINCT symptom.name) AS symptoms
            ORDER BY case.name
            LIMIT $limit
            """,
            {"device_model": device_model, "limit": limit},
        )
        evidence = [
            {
                "source_type": "knowledge_graph",
                "source_id": item["symptom"],
                "title": f"故障现象: {item['symptom']}",
                "reference": "FaultSymptom -> FaultCause -> MaintenanceAction",
                "confidence": 0.8,
            }
            for item in rows
        ]
        return {"matches": rows, "cases": cases, "evidence": evidence}

    async def path(
        self, *, symptom: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """返回故障现象到维修措施的短证据路径。"""

        return await self._query(
            """
            MATCH path=(symptom:FaultSymptom)-[:MAY_BE_CAUSED_BY]->(:FaultCause)
                -[:SOLVED_BY]->(:MaintenanceAction)
            WHERE symptom.name = $symptom
            RETURN [node IN nodes(path) | {
                id: elementId(node), type: labels(node)[0], name: node.name
            }] AS nodes,
            [relation IN relationships(path) | type(relation)] AS relationships
            LIMIT $limit
            """,
            {"symptom": symptom, "limit": limit},
        )


__all__ = ["GraphUnavailableError", "KnowledgeGraphService"]
