"""
数据库连接层基础模块。

用途：
1. 从 .env 读取数据库连接配置。
2. 创建 SQLAlchemy 2.0 风格的 engine 和 SessionLocal。
3. 暴露 Base 供后续 ORM models 继承。
4. 暴露 get_db() 供 FastAPI 路由依赖注入使用。

依赖的环境变量名：
- DATABASE_URL：数据库连接字符串
"""

from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please create a .env file based on .env.example."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 数据库会话依赖。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
