"""Neo4j 知识图谱的参数化查询服务。"""

from typing import Any

from neo4j import AsyncDriver

from ..schemas.common import EvidenceItem
from ..schemas.knowledge import (
    KnowledgeCase,
    KnowledgeMatch,
    KnowledgeNode,
    KnowledgePathResult,
    KnowledgeRelatedResult,
    KnowledgeRelationship,
)
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
        device_code: str | None = None,
    ) -> KnowledgeRelatedResult:
        """按故障现象或关键词返回原因、措施、SOP 和安全事项。"""

        normalized_keyword = keyword.strip()
        normalized_model = device_model.strip() if device_model and device_model.strip() else None
        symptom_query = """
            MATCH (symptom:FaultSymptom)
            WHERE ($keyword = '' OR toLower(symptom.name) CONTAINS toLower($keyword))
              AND (size($symptoms) = 0 OR symptom.name IN $symptoms)
              AND (
                $device_model IS NULL
                OR EXISTS {
                  MATCH (case2:MaintenanceCase)-[:ADDRESSES]->(symptom)
                  MATCH (case2)-[:APPLIES_TO]->(model2:DeviceModel)
                  WHERE model2.name = $device_model
                }
              )
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
            """
        query_parameters = {
            "device_model": normalized_model,
            "keyword": normalized_keyword,
            "symptoms": [],
            "limit": limit,
        }
        rows = await self._query(
            symptom_query,
            query_parameters,
        )
        cases = await self._query(
            """
            MATCH (case:MaintenanceCase)-[:APPLIES_TO]->(model:DeviceModel)
            MATCH (case)-[:ADDRESSES]->(symptom:FaultSymptom)
            WHERE ($device_model IS NULL OR model.name = $device_model)
              AND ($keyword = '' OR toLower(symptom.name) CONTAINS toLower($keyword))
            RETURN case.name AS name, model.name AS device_model,
                   collect(DISTINCT symptom.name) AS symptoms
            ORDER BY case.name
            LIMIT $limit
            """,
            {"device_model": normalized_model, "keyword": normalized_keyword, "limit": limit},
        )
        if normalized_keyword and normalized_model and not rows and not cases:
            # Agent 可能会用“空压机故障”这类泛化描述，而图谱只保存具体现象。
            # 先退化到该型号的历史案例，再用案例关联的具体现象补齐证据链。
            cases = await self._query(
                """
                MATCH (case:MaintenanceCase)-[:APPLIES_TO]->(model:DeviceModel)
                MATCH (case)-[:ADDRESSES]->(symptom:FaultSymptom)
                WHERE model.name = $device_model
                RETURN case.name AS name, model.name AS device_model,
                       collect(DISTINCT symptom.name) AS symptoms
                ORDER BY case.name
                LIMIT $limit
                """,
                {"device_model": normalized_model, "limit": limit},
            )
            case_symptoms = sorted(
                {
                    symptom
                    for case in cases
                    for symptom in case.get("symptoms", [])
                    if symptom
                }
            )
            if case_symptoms:
                rows = await self._query(
                    symptom_query,
                    {
                        "device_model": normalized_model,
                        "keyword": "",
                        "symptoms": case_symptoms,
                        "limit": limit,
                    },
                )
        components = await self._query(
            """
            MATCH (device:Device {code: $device_code})-[:CONTAINS]->(component:Component)
            RETURN device.code AS device_code, component.name AS name
            ORDER BY component.name
            """,
            {"device_code": device_code or ""},
        ) if device_code else []

        nodes: dict[str, KnowledgeNode] = {}
        relationships: list[KnowledgeRelationship] = []

        def add_node(node_type: str, name: str) -> str:
            node_id = f"{node_type}:{name}"
            nodes.setdefault(node_id, KnowledgeNode(id=node_id, type=node_type, name=name))
            return node_id

        for row in rows:
            symptom_id = add_node("FaultSymptom", row["symptom"])
            for cause in row["causes"]:
                cause_id = add_node("FaultCause", cause)
                relationships.append(
                    KnowledgeRelationship(
                        source_id=symptom_id, target_id=cause_id, type="MAY_BE_CAUSED_BY"
                    )
                )
                for action in row["actions"]:
                    action_id = add_node("MaintenanceAction", action)
                    relationships.append(
                        KnowledgeRelationship(
                            source_id=cause_id, target_id=action_id, type="SOLVED_BY"
                        )
                    )
                    for sop in row["sops"]:
                        relationships.append(
                            KnowledgeRelationship(
                                source_id=action_id,
                                target_id=add_node("SOP", sop),
                                type="REFER_TO",
                            )
                        )
                    for notice in row["safety_notices"]:
                        relationships.append(
                            KnowledgeRelationship(
                                source_id=action_id,
                                target_id=add_node("SafetyNotice", notice),
                                type="REQUIRES",
                            )
                        )

        case_models = [
            KnowledgeCase(
                id=f"MaintenanceCase:{row['name']}",
                name=row["name"],
                device_model=row["device_model"],
                symptoms=row["symptoms"],
            )
            for row in cases
        ]
        for case in case_models:
            case_id = add_node("MaintenanceCase", case.name)
            model_id = add_node("DeviceModel", case.device_model)
            relationships.append(
                KnowledgeRelationship(source_id=case_id, target_id=model_id, type="APPLIES_TO")
            )
            for symptom in case.symptoms:
                relationships.append(
                    KnowledgeRelationship(
                        source_id=case_id,
                        target_id=add_node("FaultSymptom", symptom),
                        type="ADDRESSES",
                    )
                )
        for component in components:
            component_id = add_node("Component", component["name"])
            device_id = add_node("Device", component["device_code"])
            relationships.append(
                KnowledgeRelationship(source_id=device_id, target_id=component_id, type="CONTAINS")
            )

        case_evidence = [
            EvidenceItem(
                source_type="knowledge_graph",
                source_id=case.id,
                title=f"历史案例: {case.name}",
                reference="MaintenanceCase -> DeviceModel / FaultSymptom",
                confidence=0.85,
                details={"device_model": case.device_model, "symptoms": case.symptoms},
            )
            for case in case_models
        ]

        return KnowledgeRelatedResult(
            nodes=list(nodes.values()),
            relationships=list({item.model_dump_json(): item for item in relationships}.values()),
            matches=[KnowledgeMatch(**row) for row in rows],
            cases=case_models,
            evidence=[
                EvidenceItem(
                    source_type="knowledge_graph",
                    source_id=item["symptom"],
                    title=f"故障现象: {item['symptom']}",
                    reference="FaultSymptom -> FaultCause -> MaintenanceAction",
                    confidence=0.8,
                )
                for item in rows
            ]
            + case_evidence,
        )

    async def path(
        self, *, symptom: str, limit: int = 10
    ) -> list[KnowledgePathResult]:
        """返回故障现象到维修措施的短证据路径。"""

        rows = await self._query(
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
        return [
            KnowledgePathResult(
                nodes=[
                    KnowledgeNode(
                        id=node["id"], type=node["type"], name=node["name"]
                    )
                    for node in row["nodes"]
                ],
                relationships=[
                    KnowledgeRelationship(
                        source_id=row["nodes"][index]["id"],
                        target_id=row["nodes"][index + 1]["id"],
                        type=relation_type,
                    )
                    for index, relation_type in enumerate(row["relationships"])
                ],
            )
            for row in rows
        ]


__all__ = ["GraphUnavailableError", "KnowledgeGraphService"]
