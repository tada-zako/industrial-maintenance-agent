"""SQLAlchemy ORM 基类和模型注册位置。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 SQLite 业务模型的声明式基类。"""
