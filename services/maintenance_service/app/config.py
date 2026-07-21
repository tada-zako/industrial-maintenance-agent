"""集中管理 maintenance-service 的环境变量和本地运行配置。"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{(SERVICE_DATA_DIR / 'maintenance.db').as_posix()}"


class Settings(BaseSettings):
    """应用配置；敏感值只从环境变量或本地未提交的 .env 读取。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "maintenance-service"
    environment: str = "development"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = DEFAULT_DATABASE_URL

    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""

    material_upload_dir: Path = SERVICE_DATA_DIR / "uploads"

    hermes_mcp_url: str = ""
    hermes_mcp_auth_token: str = ""
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ]
    )


settings = Settings()
