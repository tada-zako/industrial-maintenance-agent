"""步骤四新增 API 的集成测试。"""

import pytest

from .test_device_problem_api import api_client


@pytest.mark.asyncio
async def test_draft_dashboard_material_and_workflow_apis() -> None:
    """草案、总览和受控资料接口可构成演示闭环。"""

    async with api_client() as client:
        device_id = (await client.get("/api/devices")).json()[0]["id"]
        draft_response = await client.post(
            "/api/drafts",
            json={
                "device_id": device_id,
                "diagnosis": "冷却系统需要人工检查",
                "inspection_steps": ["确认设备停机", "检查冷却风扇"],
                "repair_steps": ["清洁风扇并复测"],
                "safety_notices": ["执行上锁挂牌并泄压"],
                "evidence": [
                    {
                        "source_type": "test",
                        "source_id": "AC-001",
                        "title": "测试状态记录",
                    }
                ],
            },
        )
        assert draft_response.status_code == 201
        draft = draft_response.json()
        assert draft["requires_human_confirmation"] is True

        update_response = await client.patch(
            f"/api/drafts/{draft['id']}/status",
            json={
                "status": "confirmed",
                "requires_human_confirmation": False,
                "review_feedback": "确认后安排受控试运行。",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "confirmed"
        assert update_response.json()["review_feedback"] == "确认后安排受控试运行。"
        assert update_response.json()["reviewed_at"] is not None

        summary_response = await client.get("/api/dashboard/summary")
        assert summary_response.status_code == 200
        assert summary_response.json()["device_count"] == 6
        assert summary_response.json()["draft_count"] == 1

        material_response = await client.post(
            "/api/materials/import",
            data={"source_description": "接口测试资料", "is_reference_allowed": "true"},
            files={"file": ("inspection.md", b"# inspection", "text/markdown")},
        )
        assert material_response.status_code == 201
        material = material_response.json()
        assert material["filename"] == "inspection.md"
        assert material["content"] == "# inspection"

        list_response = await client.get("/api/materials", params={"reference_allowed_only": True})
        assert list_response.status_code == 200
        assert any(item["id"] == material["id"] for item in list_response.json())

        delete_response = await client.delete(f"/api/materials/{material['id']}")
        assert delete_response.status_code == 204

        invalid_response = await client.post(
            "/api/materials/import",
            data={"source_description": "不支持的格式"},
            files={"file": ("script.exe", b"not executable", "application/octet-stream")},
        )
        assert invalid_response.status_code == 422

        missing_workflow = await client.get("/api/workflows/99999")
        assert missing_workflow.status_code == 404
