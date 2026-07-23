"""FastMCP 返回值和工作流输入契约测试。"""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from services.maintenance_service.app.db.models import Device, Problem
from services.maintenance_service.app.domain.enums import DeviceLifecycleStatus, WorkflowStepStatus
from services.maintenance_service.app.graph.client import GraphUnavailableError
from services.maintenance_service.app.mcp_server import (
    _as_json,
    _device_identity_error,
    _normalize_workflow_step,
    create_repair_draft,
)
from services.maintenance_service.app.schemas.knowledge import KnowledgeRelatedResult


def test_as_json_excludes_sqlalchemy_relationship_objects() -> None:
    """MCP 返回设备时不应把问题、状态等 ORM 关系对象带入 JSON。"""

    device = Device(
        id=1,
        code="TEST-AC-001",
        name="测试空压机",
        model="AC-Test",
        location="测试区域",
        status=DeviceLifecycleStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    device.problems = [Problem(id=1, device_id=1, symptom="温度过高")]

    payload = _as_json(device)

    assert payload["code"] == "TEST-AC-001"
    assert "problems" not in payload
    json.dumps(payload)


def test_normalize_workflow_step_accepts_agent_aliases() -> None:
    """工作流记录应兼容 Agent 日志中的 tool、status、note 字段。"""

    step = _normalize_workflow_step(
        {"tool": "search_knowledge", "status": "failed", "note": "Neo4j 不可用"}
    )

    assert step["step_name"] == "search_knowledge"
    assert step["tool_name"] == "search_knowledge"
    assert step["status"] is WorkflowStepStatus.FAILED
    assert step["failed"] is True
    assert step["error_message"] == "Neo4j 不可用"


def test_normalize_workflow_step_preserves_flat_agent_input_and_result() -> None:
    """Agent 使用 step/result 简写时，工作流仍应保存可读的工具轨迹。"""

    step = _normalize_workflow_step(
        {"step": "get_device_status", "device_id": 6, "result": "ok"}
    )

    assert step["step_name"] == "get_device_status"
    assert step["tool_name"] == "get_device_status"
    assert step["input_summary"] == '{"device_id": 6}'
    assert step["output_summary"] == "ok"
    assert step["status"] is WorkflowStepStatus.COMPLETED


@pytest.mark.asyncio
@pytest.mark.parametrize("graph_mode", ["empty", "unavailable"])
async def test_create_repair_draft_allows_missing_knowledge_with_warning(
    monkeypatch: pytest.MonkeyPatch, graph_mode: str
) -> None:
    """设备已确认但型号无图谱数据时，仍应保存待人工确认草案。"""

    device = SimpleNamespace(
        id=6,
        code="AC-006",
        name="六号空压机",
        model="AC-Model-C",
        is_archived=False,
    )
    draft = SimpleNamespace(
        model_dump=lambda mode="json": {"id": 101, "status": "pending_confirmation"}
    )

    class FakeKnowledgeGraphService:
        async def search(self, **_: Any) -> None:
            if graph_mode == "unavailable":
                raise GraphUnavailableError("Neo4j unavailable")
            return KnowledgeRelatedResult()

    class FakeMaintenanceService:
        def __init__(self, _: Any) -> None:
            pass

        async def get_device(self, _: int) -> Any:
            return device

        async def create_draft(self, payload: Any) -> Any:
            assert payload.requires_human_confirmation is True
            assert payload.evidence
            return draft

    @asynccontextmanager
    async def fake_session_context() -> Any:
        yield object()

    monkeypatch.setattr(
        "services.maintenance_service.app.mcp_server.session_context",
        fake_session_context,
    )
    monkeypatch.setattr(
        "services.maintenance_service.app.mcp_server.MaintenanceService", FakeMaintenanceService
    )
    monkeypatch.setattr(
        "services.maintenance_service.app.mcp_server.KnowledgeGraphService",
        FakeKnowledgeGraphService,
    )

    result = await create_repair_draft(
        device_id=6,
        device_code="AC-006",
        device_model="AC-Model-C",
        diagnosis="计划停机后未恢复",
        evidence=[{"source_type": "device_status", "title": "离线停机状态"}],
    )

    assert result["ok"] is True
    assert result["data"]["id"] == 101
    expected_warning = (
        "知识图谱当前不可用" if graph_mode == "unavailable" else "知识图谱未找到该型号"
    )
    assert any(expected_warning in warning for warning in result["warnings"])


def test_device_identity_gate_rejects_guessed_device_identifiers() -> None:
    """设备编号、名称或型号不一致时必须停止生成草案。"""

    device = Device(code="AC-001", name="一号空压机", model="AC-SCREW-75", location="一号车间")

    assert _device_identity_error(
        device_code="AC-001", device_name="一号空压机", device_model="AC-SCREW-75", actual=device
    ) is None
    assert _device_identity_error(
        device_code="AC-999", device_name=None, device_model=None, actual=device
    ) == "设备编号与已查询设备不一致，已停止生成草案。"
