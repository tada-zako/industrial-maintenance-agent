"""FastMCP 返回值和工作流输入契约测试。"""

import json
from datetime import UTC, datetime

from services.maintenance_service.app.db.models import Device, Problem
from services.maintenance_service.app.domain.enums import DeviceLifecycleStatus, WorkflowStepStatus
from services.maintenance_service.app.mcp_server import _as_json, _normalize_workflow_step


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
