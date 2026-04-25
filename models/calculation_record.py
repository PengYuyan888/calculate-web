"""
计算记录表模型。

用途：
1. 存储用户每次脚手架验算任务的基础信息、请求快照和结果快照。
2. 作为后续用户历史记录、计算书下载记录与结果追溯的数据来源。

与其他表的关系：
- 通过 user_id 外键关联 users 表的 id 字段。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class CalculationRecord(Base):
    """计算记录 ORM 模型。"""

    __tablename__ = "calculation_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="计算记录主键ID",
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="所属用户ID",
    )
    project_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="项目名称，匿名计算时可为空",
    )
    scaffold_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="脚手架类型",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="计算状态（passed或failed）",
    )
    overall_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="整体验算是否通过",
    )
    request_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="请求参数快照JSON字符串",
    )
    result_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="结果摘要快照JSON字符串",
    )
    report_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Word计算书相对路径",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间（UTC）",
    )

    user = relationship(
        "User",
        backref="calculation_records",
    )
