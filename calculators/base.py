from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple

from schemas import CalculationCheckRequest, DiagramUrls, IssueItem, ResultSummary


class BaseCalculator(ABC):
    """计算器抽象基类。"""

    def __init__(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.calculation_id = f"calc_{timestamp}"
        self.request_data: Optional[CalculationCheckRequest] = None
        self.issues: List[IssueItem] = []
        self.result_summary: Optional[ResultSummary] = None
        self.diagram_urls: Optional[DiagramUrls] = None
        self.report_download_url: Optional[str] = None

    @abstractmethod
    def calculate(
        self, request_data: CalculationCheckRequest
    ) -> Tuple[List[IssueItem], ResultSummary]:
        """执行核心计算并返回问题列表与结果摘要。"""
        pass

    @abstractmethod
    def draw_diagrams(self) -> DiagramUrls:
        """生成相关力学简图。"""
        pass

    @abstractmethod
    def generate_report(self) -> Optional[str]:
        """生成 Word 计算书并返回下载链接。"""
        pass
