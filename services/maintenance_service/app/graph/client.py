"""Neo4j 官方异步 Driver 的创建入口。"""

from neo4j import AsyncDriver, AsyncGraphDatabase

from ..config import settings


def create_driver() -> AsyncDriver:
    """创建 Neo4j 异步驱动；实际连接在知识查询阶段按需发生。"""

    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
