"""Neo4j 查询适配层测试，不要求本机启动 Neo4j。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest

from services.maintenance_service.app.graph.queries import KnowledgeGraphService


class FakeResult:
    """模拟 Neo4j 的异步记录迭代器。"""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def __aiter__(self) -> AsyncIterator["FakeRecord"]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator["FakeRecord"]:
        for row in self.rows:
            yield FakeRecord(row)


class FakeRecord:
    def __init__(self, row: dict[str, Any]) -> None:
        self.row = row

    def data(self) -> dict[str, Any]:
        return self.row


class FakeSession:
    def __init__(self) -> None:
        self.cypher = ""
        self.parameters: dict[str, Any] = {}

    async def run(self, cypher: str, parameters: dict[str, Any]) -> FakeResult:
        self.cypher = cypher
        self.parameters = parameters
        return FakeResult([{"symptom": "温度过高"}])


class FakeDriver:
    def __init__(self) -> None:
        self.fake_session = FakeSession()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[FakeSession]:
        yield self.fake_session


@pytest.mark.asyncio
async def test_graph_query_passes_values_as_parameters() -> None:
    """图谱适配层只把变量作为参数传入，而不是拼接到 Cypher 字符串。"""

    driver = FakeDriver()
    rows = await KnowledgeGraphService()._query_with_driver(
        driver, "MATCH (n) WHERE n.name = $name RETURN n", {"name": "AC-001"}
    )

    assert rows == [{"symptom": "温度过高"}]
    assert "$name" in driver.fake_session.cypher
    assert driver.fake_session.parameters == {"name": "AC-001"}


@pytest.mark.asyncio
async def test_knowledge_search_filters_cases_by_model_and_keyword(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """案例查询必须同时约束设备型号和故障现象，避免串出其他型号的证据。"""

    service = KnowledgeGraphService()
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_query(cypher: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        calls.append((cypher, parameters))
        if "RETURN case.name" in cypher:
            return [
                {
                    "name": "夏季高温案例",
                    "device_model": "AC-Model-A",
                    "symptoms": ["温度过高"],
                }
            ]
        if "FaultSymptom" in cypher:
            return [
                {
                    "symptom": "温度过高",
                    "causes": ["冷却风扇效率下降"],
                    "actions": ["检查并清洁冷却风扇"],
                    "sops": ["空压机停机检查 SOP"],
                    "safety_notices": ["停机、泄压并执行上锁挂牌后再检查"],
                }
            ]
        return []

    monkeypatch.setattr(service, "_query", fake_query)
    result = await service.search(keyword=" 温度过高 ", device_model=" AC-Model-A ")

    assert [item.device_model for item in result.cases] == ["AC-Model-A"]
    symptom_query, symptom_parameters = next(
        (cypher, parameters) for cypher, parameters in calls if "FaultSymptom" in cypher
    )
    assert "model2.name = $device_model" in symptom_query
    assert symptom_parameters["device_model"] == "AC-Model-A"
    case_query, case_parameters = next(
        (cypher, parameters) for cypher, parameters in calls if "RETURN case.name" in cypher
    )
    assert "model.name = $device_model" in case_query
    assert "symptom.name) CONTAINS toLower($keyword)" in case_query
    assert case_parameters == {
        "device_model": "AC-Model-A",
        "keyword": "温度过高",
        "limit": 20,
    }


@pytest.mark.asyncio
async def test_knowledge_search_falls_back_to_model_case_for_generic_keyword(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """泛化诊断词无直接匹配时，应返回已确认型号的案例和具体证据。"""

    service = KnowledgeGraphService()
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_query(cypher: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        calls.append((cypher, parameters))
        if "RETURN case.name" in cypher:
            if parameters.get("keyword"):
                return []
            return [
                {
                    "name": "阀门磨损案例",
                    "device_model": "AC-Model-B",
                    "symptoms": ["排气压力异常"],
                }
            ]
        if "FaultSymptom" in cypher:
            if parameters.get("keyword"):
                return []
            return [
                {
                    "symptom": "排气压力异常",
                    "causes": ["排气阀磨损"],
                    "actions": ["检查排气阀并按手册更换"],
                    "sops": ["排气系统检查 SOP"],
                    "safety_notices": ["确认压力归零，佩戴防护用品"],
                }
            ]
        return []

    monkeypatch.setattr(service, "_query", fake_query)
    result = await service.search(keyword="空压机故障", device_model="AC-Model-B")

    assert [item.name for item in result.cases] == ["阀门磨损案例"]
    assert [item.symptom for item in result.matches] == ["排气压力异常"]
    assert any(item.source_id == "MaintenanceCase:阀门磨损案例" for item in result.evidence)
    assert any(
        parameters == {"device_model": "AC-Model-B", "limit": 20}
        for cypher, parameters in calls
        if "RETURN case.name" in cypher and "AND ($keyword" not in cypher
    )
