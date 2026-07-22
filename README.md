# 多工具调用工业运维 Agent Demo

这是一个面向生产实习展示的本地 Demo。项目使用工业空压机 Mock 数据，演示 Hermes Agent 通过 FastMCP 调用设备查询、故障检索、知识图谱、维修资料和维修草案工具，并通过 Vue 运维看板查看结果。

项目不连接真实设备，不控制 PLC，不面向高并发或长期生产运行。

## 技术架构

```text
Vue 3 + Element Plus + ECharts
          │ HTTP
          ▼
FastAPI + SQLAlchemy Async ORM + SQLite
          │                 │
          │                 └── Neo4j 知识图谱
          │
          └── FastMCP（Hermes 调用）
                         ▲
                         │ MCP
                   Hermes Agent
```

主要目录：

```text
services/maintenance_service/
  app/api/       FastAPI 浏览器接口
  app/db/        SQLAlchemy Async ORM、SQLite 模型和仓储
  app/domain/    FastAPI/FastMCP 共用业务逻辑
  app/graph/     Neo4j 异步查询和初始化
  app/mcp_server.py  FastMCP 工具入口
  data/mock/     可重复初始化的 Mock 数据
frontend/       Vue 3 + TypeScript + Vite 看板
compose.yml     Docker Compose 本地编排
docs/            需求和开发目标说明
```

## Docker 启动

需要先安装 Docker Desktop，并确保 Docker Engine 正在运行。首次运行可以复制配置示例：

```powershell
Copy-Item .env.example .env
```

然后按需修改 `.env` 中的密码。启动全部服务：

```powershell
docker compose up -d --build
docker compose ps
```

Compose 会启动 Hermes、FastAPI/FastMCP、Vue 前端和 Neo4j。首次启动会初始化 SQLite Mock 数据和 Neo4j 示例知识图谱。

请在首次启动前确定 `.env` 中的 `NEO4J_PASSWORD`。Neo4j 数据卷只会在第一次初始化时设置密码，后续修改环境变量不会自动修改已有数据卷的密码；已有数据卷需要使用原密码同步，或在确认数据可重建后单独重建 Neo4j 数据卷。

## 访问地址

| 服务 | 地址 | 用途 |
|---|---|---|
| Vue 运维看板 | [http://127.0.0.1:3000](http://127.0.0.1:3000) | 设备、问题、资料、草案和工作流 |
| Hermes Web Dashboard | [http://127.0.0.1:9119](http://127.0.0.1:9119) | Hermes 对话、Provider 和模型配置 |
| FastAPI | [http://127.0.0.1:8000](http://127.0.0.1:8000) | 浏览器业务 API |
| FastAPI 健康检查 | [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) | 维护服务状态 |
| Hermes API 健康检查 | [http://127.0.0.1:8000/api/hermes/health](http://127.0.0.1:8000/api/hermes/health) | 后端代理检查 Hermes API 状态 |
| Neo4j Browser | [http://127.0.0.1:7474](http://127.0.0.1:7474) | 可选的知识图谱查看 |

`8642` 是 Hermes API，不是 Web UI。直接访问 `http://127.0.0.1:8642/` 返回 404 属于正常现象；浏览器看板通过 FastAPI 代理检查它，用户对话和 Provider 配置使用 `9119` Dashboard。

Hermes Dashboard 默认使用 `.env` 中的以下本地认证配置：

```text
HERMES_DASHBOARD_BASIC_AUTH_USERNAME
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD
HERMES_DASHBOARD_BASIC_AUTH_SECRET
```

这是本地 Demo 的访问保护。不要将真实密码或 Provider API Key 提交到 Git。

## Provider API 配置

本项目不重复实现 Provider API 配置页面，也不把 Provider 密钥保存到项目 SQLite。启动后：

1. 打开 Vue 看板的“**Hermes 助手**”页面；
2. 点击“**配置 Provider API**”或直接打开 Hermes Dashboard；
3. 在 Hermes 自带界面中配置 Provider、模型和 API Key；
4. 回到看板，使用示例问题进入 Hermes 对话。

Hermes 的 MCP 服务会在容器启动时注册为 `maintenance`，内部地址为 `http://maintenance-mcp:8001/mcp`。

## 推荐演示流程

1. 在“设备管理”查看设备运行状态，必要时新增或修改一台 Mock 设备；
2. 在“问题中心”查看待处理故障；
3. 在“运维资料”导入一份 `md`、`txt`、`json`、`csv`、`pdf` 或 `docx` 资料；
4. 在 Hermes 中提出设备故障问题；
5. 观察 Hermes 调用多个 MCP 工具，查询设备、问题、知识图谱和维修资料；
6. 回到看板查看维修草案、证据、安全注意事项和工作流时间线；
7. 在草案页面执行人工确认或归档。

## 本地前端开发

前端依赖使用 pnpm，默认使用真实 FastAPI 接口：

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm run dev
```

前端环境变量参见 [frontend/.env.example](frontend/.env.example)。Docker 构建时则使用根目录 `.env` 传入的 `VITE_*` 变量。

## 后端本地开发

根目录 Python 依赖使用 uv，数据库访问必须保持异步 SQLAlchemy + `aiosqlite`：

```powershell
uv run python -m services.maintenance_service.app.db.seed
uv run uvicorn services.maintenance_service.app.main:app --reload --port 8000
```

FastMCP 服务：

```powershell
uv run python -m services.maintenance_service.app.mcp_server
```

## 停止和清理

只停止服务并保留演示数据：

```powershell
docker compose down
```

删除本项目 Compose 容器、网络和命名卷，包括 SQLite、Neo4j 和 Hermes 配置数据：

```powershell
docker compose down -v --remove-orphans
```

不要使用面向整个 Docker 环境的全局清理命令。

## 项目边界

- 不修改 Hermes 源码；
- 不重新开发 Agent 对话页面；
- 不接入真实 PLC、传感器或执行设备；
- 不引入 Redis、PostgreSQL、向量数据库或复杂权限系统；
- 外部资料只做受控保存和参考，不自动联网采集或执行上传内容；
- 维修方案是需要人工确认的草案，不能作为现场操作指令。

更详细的范围、数据模型、知识图谱和验收说明见：

- [项目需求文档](docs/项目需求文档-多工具调用工业运维Agent.md)
- [批次一：系统架构与技术栈](docs/开发目标文档-批次1-系统架构与技术栈.md)
- [批次二：数据与知识图谱](docs/开发目标文档-批次2-数据与知识图谱.md)
- [批次三：前端与项目验收](docs/开发目标文档-批次3-前端与项目验收.md)
- [后端服务说明](services/maintenance_service/README.md)
