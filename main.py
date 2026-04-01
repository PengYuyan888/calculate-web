from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from calculators.exterior_scaffold import ExteriorScaffoldCalculator
from schemas import CalculationCheckRequest, CalculationCheckResponse


app = FastAPI(
    title="轻量化脚手架安全计算软件",
    version="0.1.0",
    description="MVP 阶段盘扣式双排外脚手架验算接口骨架",
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.post(
    "/api/v1/calculations/exterior-scaffold/check",
    response_model=CalculationCheckResponse,
    summary="盘扣式双排外脚手架验算",
)
async def check_exterior_scaffold(
    request_data: CalculationCheckRequest,
) -> CalculationCheckResponse:
    calculator = ExteriorScaffoldCalculator()
    issues, result_summary = calculator.calculate(request_data)
    diagram_urls = calculator.draw_diagrams()
    report_download_url = calculator.generate_report()

    status_value = "success" if result_summary.overall_passed else "failed"
    message = (
        "验算完成，所有核心校核项均满足要求。"
        if result_summary.overall_passed
        else "验算未通过，请根据提示调整参数后重试。"
    )

    return CalculationCheckResponse(
        status=status_value,
        message=message,
        calculation_id=calculator.calculation_id,
        result_summary=result_summary,
        issues=issues,
        diagram_urls=diagram_urls,
        report_download_url=report_download_url,
        generated_at=datetime.now().astimezone(),
    )
