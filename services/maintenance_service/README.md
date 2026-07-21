# maintenance-service

阶段一、二的独立后端服务边界，同时承载 FastAPI HTTP 接口、FastMCP 工具入口、共享业务服务、SQLite 和 Neo4j 访问。

当前仅完成启动骨架和 `/api/health`；设备模型、CRUD、知识图谱初始化及 MCP 工具按开发任务分步实现。

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

## 目录职责

- `app/api`：浏览器使用的 FastAPI 路由；
- `app/db`：SQLAlchemy Async ORM、SQLite 模型、Session 和仓储；
- `app/graph`：Neo4j 异步 Driver、Cypher 查询和图谱初始化；
- `app/domain`：FastAPI 与 FastMCP 共用的业务服务和工作流；
- `app/schemas`：Pydantic 请求与响应模型；
- `data/mock`：可重复初始化的 AI Mock 数据；
- `data/uploads`：受控外部资料导入目录；
- `tests`：后端单元测试和接口测试。
