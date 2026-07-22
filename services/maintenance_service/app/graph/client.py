"""Neo4j 官方异步 Driver 的创建和受控生命周期。"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from neo4j import AsyncDriver, AsyncGraphDatabase

from ..config import settings

logger = logging.getLogger(__name__)


class GraphUnavailableError(Exception):
    """Neo4j 不可用时向 HTTP 和 MCP 返回的受控错误。"""


def create_driver() -> AsyncDriver:
    """创建 Neo4j 异步驱动；实际连接在知识查询阶段按需发生。"""

    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )


@asynccontextmanager
async def graph_driver() -> AsyncIterator[AsyncDriver]:
    """按查询创建和关闭 Driver，避免泄露连接或向调用方暴露底层异常。"""

    driver = create_driver()
    try:
        await driver.verify_connectivity()
        yield driver
    except GraphUnavailableError:
        raise
    except Exception as exc:
        # 日志保留异常类型，帮助区分认证失败、网络失败和数据库未启动；不向浏览器暴露底层细节。
        logger.warning("Neo4j connectivity check failed: %s: %s", type(exc).__name__, exc)
        raise GraphUnavailableError("知识图谱服务暂不可用，请稍后重试") from exc
    finally:
        await driver.close()
