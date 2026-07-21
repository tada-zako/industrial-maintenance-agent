# AGENTS.md

## Progressive disclosure for project documents

Do not read all project documents at the start of every task. Read only the document section relevant to the current task, when that task requires the detail.

- [Project requirements](docs/项目需求文档-多工具调用工业运维Agent.md): overall goals, constraints, deployment approach, and final product definition. Read when the task changes project scope, architecture, deployment, or acceptance criteria.
- [Batch 1: architecture and stack](docs/开发目标文档-批次1-系统架构与技术栈.md): technology choices and frontend/backend boundaries. Read when adding a service, changing dependencies, or deciding where code belongs.
- [Batch 2: data and knowledge graph](docs/开发目标文档-批次2-数据与知识图谱.md): data sources, SQLite/Neo4j responsibilities, entities, relationships, CRUD, and MCP workflow. Read when changing models, repositories, seed data, graph queries, or MCP tools.
- [Batch 3: frontend and acceptance](docs/开发目标文档-批次3-前端与项目验收.md): pages, API contracts, CRUD endpoints, Compose services, tests, and demo acceptance. Read when implementing frontend pages, HTTP APIs, integration tests, or deployment changes.

These documents are the detailed source of truth. Do not duplicate their specifications in this file. If a task touches multiple areas, read the smallest relevant subset of the corresponding documents.

## Project rule

This is a small, local, production-internship demo. Optimize for a clear, runnable MVP and a complete demonstration flow. Do not design for high concurrency, long-term product maintenance, multi-tenancy, production security governance, or real factory control.

When a requirement is ambiguous, choose the smallest safe implementation that preserves the documented demo flow. Do not add infrastructure or abstractions speculatively.

## Fixed architecture

- Hermes Agent: runtime, natural-language reasoning, and MCP tool calling.
- FastMCP: Agent-facing maintenance tools.
- FastAPI: browser-facing HTTP API.
- SQLite: primary CRUD database.
- SQLAlchemy 2.x Async ORM + `aiosqlite`: the required SQLite access layer.
- Neo4j: the small knowledge-graph store; use the official async Python driver.
- Vue 3 + TypeScript + Vite + Vue Router + Element Plus + ECharts: frontend.
- Docker Compose: local orchestration.

Do not modify Hermes source code or build a second chat UI. The browser must access FastAPI, not Neo4j or MCP directly.

## Implementation rules

### Backend

- Use `async def` for FastAPI handlers and I/O-bound MCP tools.
- Use `AsyncEngine`, `async_sessionmaker`, and `AsyncSession` with a URL such as `sqlite+aiosqlite:///...`.
- Never use synchronous `sqlite3` or synchronous SQLAlchemy sessions in an async request/tool path.
- Keep route handlers thin; put shared behavior in small service functions used by FastAPI and FastMCP.
- Validate inputs with Pydantic schemas and use parameterized SQLAlchemy/Cypher queries.
- Keep IDs, statuses, timestamps, and source metadata explicit.
- Prefer simple initialization/seed scripts. Do not add migrations, queues, caches, or extra databases unless required by an actual change.

### Frontend

- Use Vue 3 Composition API and TypeScript.
- Use Element Plus for basic UI components; do not rebuild tables, forms, dialogs, or timelines from scratch.
- Use a small Fetch wrapper and composables for API calls. Do not add TanStack Query or Pinia by default.
- Every async view must handle loading, empty, success, and error states.
- Keep request logic out of templates and avoid `any` for normal domain data.

### Comments

Add concise Chinese comments or docstrings at necessary locations, especially for:

- important modules;
- database models and session management;
- public classes and functions;
- MCP tools and API handlers;
- non-obvious workflow or safety decisions.

Comments should explain project-specific intent or reason. Do not comment obvious code line by line.

## Security and data boundaries

- Never commit secrets, tokens, passwords, or private source documents.
- Read local configuration from environment variables; update `.env.example` when needed.
- Keep local services bound to `127.0.0.1` unless exposure is explicitly required.
- Treat mock and imported materials as untrusted reference data; preserve source metadata.
- Validate uploaded file type, size, filename, and destination. Prevent path traversal and never execute uploaded content.
- Do not interpolate user input into SQL or Cypher.
- Do not expose database credentials, stack traces, or internal paths to the browser.
- Repair plans are drafts requiring human confirmation; no tool may control real equipment.

## Verification

Before reporting a change as complete:

1. Run the relevant backend/frontend tests.
2. Check the changed API, MCP tool, or page with representative data.
3. For integration changes, validate Compose configuration:

   ```powershell
   docker compose -f compose.yml config --quiet
   ```

4. Verify that the documented demo flow still works.
5. Report untested integrations explicitly; do not claim production reliability.

Use the detailed acceptance checklist in [Batch 3](docs/开发目标文档-批次3-前端与项目验收.md). For commands, ports, environment variables, and cleanup procedures, follow `compose.yml`, `.env.example`, and the project documents rather than inventing new defaults.
