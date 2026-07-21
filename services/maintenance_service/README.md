# maintenance-service

阶段一、二的独立后端服务边界，同时承载 FastAPI HTTP 接口、FastMCP 工具入口、共享业务服务、SQLite 和 Neo4j 访问。

当前已完成启动骨架、`/api/health`、SQLite 数据模型和 Pydantic 数据契约；Mock 数据、CRUD、知识图谱初始化及 MCP 工具按开发任务分步实现。

步骤一已建立以下 SQLite 表：`devices`、`device_statuses`、`problems`、`maintenance_drafts`、`workflow_runs`、`workflow_steps`、`external_materials` 和 `audit_records`。数据库默认使用异步 SQLAlchemy + `aiosqlite`，数据文件位于服务目录的 `data/maintenance.db`。

## 本地启动

在项目根目录执行：

```powershell
uv run uvicorn services.maintenance_service.app.main:app --reload --port 8000
```

健康检查：`http://127.0.0.1:8000/api/health`

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
