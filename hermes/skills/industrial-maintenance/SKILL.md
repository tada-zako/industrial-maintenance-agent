---
name: mcp-maintenance
description: 工业设备维修 MCP 工具链。只使用 maintenance MCP 工具完成设备查询、草案生成和工作流记录。
tags:
  - mcp
  - maintenance
  - industrial
---

# 工业运维 MCP 工作流

本项目运行在 Docker Compose 中。维修数据必须通过 `maintenance` MCP 服务处理，不能把容器内文件当作用户可用的维修成果。

## 强制边界

- 只调用 maintenance MCP 暴露的工具：`list_devices`、`get_device_status`、`search_problems`、`search_knowledge`、`get_maintenance_material`、`create_repair_draft`、`validate_repair_draft`、`record_workflow_run`。
- 不要调用 `terminal`、`write_file`、`read_file`、`patch`、`search_files` 或 `session_search` 作为本工作流的降级手段。
- 不要创建本地 Markdown、日志、Python 脚本、MCP 客户端或新的 MCP 工具。
- 不要手动拼接 Streamable HTTP 请求，也不要用 curl 探测 `/mcp`；MCP 客户端负责建立会话。
- MCP 工具失败时，直接向用户说明失败原因或需要补充的信息；不要伪造 MCP 结果，也不要切换到本地文件方案。
- 旧会话、旧记忆或旧维修文件中的本地降级建议已经废弃，不要据此恢复文件降级流程。
- 维修草案始终是待人工确认的记录，不执行真实设备控制。

## 标准流程

1. 使用 `list_devices` 根据用户提供的设备编号、名称或型号确认设备，不猜测 `device_id`。
2. 使用 `get_device_status` 查询已确认设备的最新状态。
3. 使用 `search_problems(device_id=...)` 查询历史问题。
4. 使用状态中的具体故障现象调用 `search_knowledge`，并传入已确认的 `device_model`。
5. 使用 `get_maintenance_material` 查询允许参考的资料。
6. 设备身份已确认后调用 `create_repair_draft`。知识图谱没有该型号的匹配案例时，仍然可以创建草案；将设备状态、问题记录等已获得信息作为 `evidence`，并向用户说明知识证据缺失。
7. 创建成功后调用 `validate_repair_draft`。
8. 最后调用 `record_workflow_run`，记录真实的工具、输入、输出、状态和证据。

## 工作流步骤格式

推荐使用下面的结构记录步骤，不要只传“工具调用已完成”：

```json
{
  "step": "get_device_status",
  "input": {"device_id": 6},
  "output": {"ok": true, "status": "offline"},
  "status": "completed",
  "evidence": []
}
```

失败步骤必须设置 `status: "failed"`、`failed: true` 或 `error_message`，并保留工具返回的错误摘要。不要把 API Key、完整原始响应或无关敏感内容写入工作流。

## 知识证据不足时

`search_knowledge` 返回空结果只表示当前关键词或型号没有匹配，不代表服务可以被替换成本地文件流程。设备身份确认后，继续调用 `create_repair_draft`，使用已确认的设备状态和问题证据，并保留“知识图谱证据缺失”的告警。草案可以创建，但后续校验和人工确认仍然是必需的。
