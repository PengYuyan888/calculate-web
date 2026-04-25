from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from calculators.exterior_scaffold import ExteriorScaffoldCalculator
from routers.auth import router as auth_router
from routers.history import router as history_router
from schemas import (
    CalculationCheckRequest,
    CalculationCheckResponse,
    WindParamsResolveRequest,
    WindParamsResolveResponse,
)
from database import get_db
from services.auth import get_current_user
from services.wind_reference import (
    get_all_locations,
    resolve_wind_params as resolve_reference_wind_params,
)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(
    title="Calculate Web API",
    version="0.1.0",
    description="Ringlock double-row exterior scaffold calculation API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(history_router)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/specs-files", StaticFiles(directory=BASE_DIR / "docs"), name="specs_files")


def _hydrate_wind_params(request_data: CalculationCheckRequest) -> None:
    material_params = request_data.material_load_params
    location_info = request_data.location_info

    needs_auto_resolution = (
        material_params.basic_wind_pressure_w0_kn_m2 is None
        or material_params.wind_height_factor_muz is None
    )

    if location_info is not None and needs_auto_resolution:
        try:
            resolved = resolve_reference_wind_params(
                province=location_info.province,
                city=location_info.city,
                code=location_info.code,
                roughness=material_params.terrain_roughness_category,
                erection_height_hs_m=request_data.geometry_params.erection_height_hs_m,
            )

            if material_params.basic_wind_pressure_w0_kn_m2 is None:
                material_params.basic_wind_pressure_w0_kn_m2 = float(
                    resolved["w0_kn_m2"]
                )

            if material_params.wind_height_factor_muz is None:
                material_params.wind_height_factor_muz = float(
                    resolved["wind_height_factor_muz"]
                )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    missing_fields: list[str] = []
    if material_params.basic_wind_pressure_w0_kn_m2 is None:
        missing_fields.append("material_load_params.basic_wind_pressure_w0_kn_m2")
    if material_params.wind_height_factor_muz is None:
        missing_fields.append("material_load_params.wind_height_factor_muz")

    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=(
                "Missing wind-load parameters. Provide location_info or fill in "
                "basic_wind_pressure_w0_kn_m2 and wind_height_factor_muz manually. "
                f"Missing fields: {', '.join(missing_fields)}"
            ),
        )


@app.get(
    "/api/v1/reference/locations",
    summary="Get province/city reference data",
)
async def get_reference_locations() -> dict:
    return get_all_locations()


@app.post(
    "/api/v1/reference/wind-params/resolve",
    response_model=WindParamsResolveResponse,
    summary="Resolve basic wind pressure and wind height factor",
)
async def resolve_wind_params(
    request_data: WindParamsResolveRequest,
) -> WindParamsResolveResponse:
    try:
        resolved = resolve_reference_wind_params(
            province=request_data.province,
            city=request_data.city,
            code=request_data.code,
            roughness=request_data.roughness,
            erection_height_hs_m=request_data.erection_height_hs_m,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return WindParamsResolveResponse(
        w0_kn_m2=round(float(resolved["w0_kn_m2"]), 3),
        altitude_m=round(float(resolved["altitude_m"]), 1),
        effective_height_m=round(float(resolved["effective_height_m"]), 1),
        wind_height_factor_muz=round(float(resolved["wind_height_factor_muz"]), 3),
        matched_city=str(resolved["matched_city"]),
        match_type=str(resolved["match_type"]),
        distance_km=(
            round(float(resolved["distance_km"]), 1)
            if resolved["distance_km"] is not None
            else None
        ),
        is_fallback=bool(resolved["is_fallback"]),
    )


@app.post(
    "/api/v1/calculations/exterior-scaffold/check",
    response_model=CalculationCheckResponse,
    summary="Run exterior scaffold checks",
)
async def check_exterior_scaffold(
    request_data: CalculationCheckRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> CalculationCheckResponse:
    _hydrate_wind_params(request_data)

    current_user = None
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token:
        current_user = get_current_user(token, db)

    calculator = ExteriorScaffoldCalculator()
    issues, result_summary = calculator.calculate(
        request_data,
        db=db if current_user is not None else None,
        user_id=current_user.id if current_user is not None else None,
    )
    diagram_urls = calculator.draw_diagrams()
    report_download_url = calculator.generate_report()

    status_value = "success" if result_summary.overall_passed else "failed"
    message = (
        "Calculation finished successfully."
        if result_summary.overall_passed
        else "Calculation failed. Please adjust the inputs and try again."
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
