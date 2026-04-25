"""
历史记录路由模块。

用途：
1. 提供当前登录用户的验算历史列表查询接口。
2. 提供当前登录用户的单条历史记录详情查询接口。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database import get_db
from models.calculation_record import CalculationRecord
from models.user import User
from services.auth import require_current_user


router = APIRouter(prefix="/api/v1/history", tags=["history"])
BASE_DIR = Path(__file__).resolve().parent.parent


class HistoryListItemResponse(BaseModel):
    id: int = Field(..., description="历史记录ID")
    project_name: str | None = Field(..., description="项目名称")
    scaffold_type: str = Field(..., description="脚手架类型")
    status: str = Field(..., description="计算状态")
    overall_passed: bool = Field(..., description="整体验算是否通过")
    created_at: datetime = Field(..., description="记录创建时间")
    report_path: str | None = Field(..., description="Word计算书相对路径")


class HistoryDetailResponse(BaseModel):
    id: int = Field(..., description="历史记录ID")
    project_name: str | None = Field(..., description="项目名称")
    scaffold_type: str = Field(..., description="脚手架类型")
    status: str = Field(..., description="计算状态")
    overall_passed: bool = Field(..., description="整体验算是否通过")
    request_snapshot: str | None = Field(..., description="请求参数快照JSON字符串")
    result_snapshot: str | None = Field(..., description="结果摘要快照JSON字符串")
    report_path: str | None = Field(..., description="Word计算书相对路径")
    created_at: datetime = Field(..., description="记录创建时间")


class HistoryDeleteResponse(BaseModel):
    message: str = Field(..., description="删除结果提示信息")


@router.get(
    "/",
    response_model=list[HistoryListItemResponse],
    summary="获取当前用户验算历史列表",
)
def get_history_list(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[HistoryListItemResponse]:
    statement = (
        select(CalculationRecord)
        .where(CalculationRecord.user_id == current_user.id)
        .order_by(desc(CalculationRecord.created_at))
        .limit(50)
    )
    records = db.scalars(statement).all()

    return [
        HistoryListItemResponse(
            id=record.id,
            project_name=record.project_name,
            scaffold_type=record.scaffold_type,
            status=record.status,
            overall_passed=record.overall_passed,
            created_at=record.created_at,
            report_path=record.report_path,
        )
        for record in records
    ]


@router.get(
    "/{record_id}",
    response_model=HistoryDetailResponse,
    summary="获取当前用户单条验算历史详情",
)
def get_history_detail(
    record_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> HistoryDetailResponse:
    statement = select(CalculationRecord).where(
        CalculationRecord.id == record_id,
        CalculationRecord.user_id == current_user.id,
    )
    record = db.scalar(statement)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在",
        )

    return HistoryDetailResponse(
        id=record.id,
        project_name=record.project_name,
        scaffold_type=record.scaffold_type,
        status=record.status,
        overall_passed=record.overall_passed,
        request_snapshot=record.request_snapshot,
        result_snapshot=record.result_snapshot,
        report_path=record.report_path,
        created_at=record.created_at,
    )


@router.delete(
    "/{record_id}",
    response_model=HistoryDeleteResponse,
    summary="删除当前用户单条验算历史记录",
)
def delete_history_record(
    record_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> HistoryDeleteResponse:
    statement = select(CalculationRecord).where(
        CalculationRecord.id == record_id,
        CalculationRecord.user_id == current_user.id,
    )
    record = db.scalar(statement)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在",
        )

    if record.report_path:
        report_file_path = BASE_DIR / record.report_path.lstrip("/")
        try:
            report_file_path.unlink()
        except FileNotFoundError:
            pass

    db.delete(record)
    db.commit()
    return HistoryDeleteResponse(message="删除成功")
