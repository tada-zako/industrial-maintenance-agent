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
