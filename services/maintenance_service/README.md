# maintenance-service

## 运行接口

- FastAPI: `http://127.0.0.1:8000`，提供设备、问题、草案、资料、工作流和看板接口。
- FastMCP: `http://127.0.0.1:8001/mcp`，提供 8 个设备运维查询、草案和工作流记录工具。

维修草案仅用于人工审核；服务和 MCP 工具都不会控制实际设备。Compose 会将 MCP 地址通过 `MAINTENANCE_MCP_URL` 传递给 Hermes 容器，注册时使用 Streamable HTTP 地址即可。

阶段一、二的独立后端服务边界，同时承载 FastAPI HTTP 接口、FastMCP 工具入口、共享业务服务、SQLite 和 Neo4j 访问。

当前已完成 `/api/health`、`/api/hermes/health`、SQLite 数据模型、Mock 数据初始化、共享 Repository/domain 服务、设备/问题/草案/资料/工作流 FastAPI API、知识图谱查询和 MCP 工具。资料上传仅保存受控文件和元数据，不执行文件内容。

步骤一已建立以下 SQLite 表：`devices`、`device_statuses`、`problems`、`maintenance_drafts`、`workflow_runs`、`workflow_steps`、`external_materials` 和 `audit_records`。数据库默认使用异步 SQLAlchemy + `aiosqlite`，数据文件位于服务目录的 `data/maintenance.db`。

## 本地启动

在项目根目录执行：

```powershell
uv run uvicorn services.maintenance_service.app.main:app --reload --port 8000
```

健康检查：`http://127.0.0.1:8000/api/health`；Hermes 代理检查：`http://127.0.0.1:8000/api/hermes/health`

当前已提供设备、设备状态、问题、维修草案、外部资料、工作流和看板接口；设备、问题和草案的删除操作采用归档，不物理删除历史记录。外部资料通过 `/api/materials/import` 受控导入，通过 `/api/materials` 查询。

FastMCP 入口：

```powershell
uv run python -m services.maintenance_service.app.mcp_server
```

初始化 SQLite 表结构并导入 Mock 数据：

```powershell
uv run python -m services.maintenance_service.app.db.seed
```

## 目录职责

- `app/api`：浏览器使用的 FastAPI 路由；
- `app/db`：SQLAlchemy Async ORM、SQLite 模型、Session 和仓储；
- `app/graph`：Neo4j 异步 Driver、Cypher 查询和图谱初始化；
- `app/domain`：FastAPI 与 FastMCP 共用的业务服务和工作流；
- `app/schemas`：Pydantic 请求与响应模型；
- `data/mock`：可重复初始化的 AI Mock 数据；
- `data/uploads`：受控外部资料导入目录；
- `tests`：后端单元测试和接口测试。
