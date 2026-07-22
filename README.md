# 工业运维多工具调用 Demo

本项目使用工业空压机 Mock 数据，逐步实现 Hermes Agent、FastMCP、FastAPI、SQLite 和 Neo4j 的多工具调用演示闭环。

## 当前结构

```text
services/maintenance_service/
  app/
    api/       FastAPI HTTP 路由
    db/        SQLAlchemy Async ORM 与 SQLite
    graph/     Neo4j 异步 Driver、查询和初始化
    domain/    FastAPI/FastMCP 共用业务服务
    schemas/   Pydantic 请求与响应模型
  data/        Mock 数据与受控资料目录
  tests/       后端测试
frontend/      后续阶段的 Vue 前端目录
```

后端启动说明见 [services/maintenance_service/README.md](services/maintenance_service/README.md)，依赖由根目录 `uv` 项目和 `.venv` 统一管理。

本轮只完成依赖、配置示例和后端启动骨架；业务模型、CRUD、知识图谱数据和 MCP 工具按阶段一、二分步实现。
