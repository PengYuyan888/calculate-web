from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage, RichText
from sqlalchemy.orm import Session

from calculators.base import BaseCalculator
from models.calculation_record import CalculationRecord
from schemas import CalculationCheckRequest, DiagramUrls, IssueItem, ResultSummary

# 设置中文字体，防止图表中的中文显示为方块
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 13
plt.rcParams["xtick.labelsize"] = 11
plt.rcParams["ytick.labelsize"] = 11
plt.rcParams["legend.fontsize"] = 11


def _build_stability_table(raw: str) -> List[float]:
    """Parse appendix-C rows into a lambda-indexed lookup list."""
    table: List[float] = []
    for line in raw.strip().splitlines():
        parts = line.split()
        base_lambda = int(parts[0])
        if base_lambda != len(table):
            raise ValueError(f"Unexpected appendix-C row start: {base_lambda}")
        for offset, phi in enumerate(parts[1:]):
            expected_lambda = base_lambda + offset
            if expected_lambda != len(table):
                raise ValueError(f"Unexpected appendix-C lambda index: {expected_lambda}")
            table.append(float(phi))
    return table


# Appendix C stability coefficient tables used by the vertical standard check.
# Index position matches the slenderness ratio λ directly.
_STABILITY_FACTOR_TABLES = {
    "Q235": _build_stability_table(
        """
        0 1.000 0.997 0.995 0.992 0.989 0.987 0.984 0.981 0.979 0.976
        10 0.974 0.971 0.968 0.969 0.963 0.960 0.958 0.955 0.952 0.949
        20 0.947 0.944 0.941 0.938 0.936 0.933 0.930 0.927 0.924 0.921
        30 0.918 0.915 0.912 0.909 0.906 0.903 0.899 0.896 0.893 0.889
        40 0.886 0.882 0.879 0.875 0.872 0.868 0.864 0.861 0.858 0.855
        50 0.852 0.849 0.846 0.843 0.839 0.836 0.832 0.829 0.825 0.822
        60 0.818 0.814 0.810 0.806 0.802 0.797 0.793 0.789 0.784 0.779
        70 0.775 0.770 0.765 0.760 0.755 0.750 0.744 0.739 0.733 0.728
        80 0.722 0.716 0.710 0.704 0.698 0.692 0.686 0.680 0.673 0.667
        90 0.661 0.654 0.648 0.641 0.634 0.626 0.618 0.611 0.603 0.595
        100 0.588 0.580 0.573 0.566 0.558 0.551 0.544 0.537 0.530 0.523
        110 0.516 0.509 0.502 0.496 0.489 0.483 0.476 0.470 0.464 0.458
        120 0.452 0.446 0.440 0.434 0.428 0.423 0.417 0.412 0.406 0.401
        130 0.396 0.391 0.386 0.381 0.376 0.371 0.367 0.362 0.357 0.353
        140 0.349 0.344 0.340 0.336 0.332 0.328 0.324 0.320 0.316 0.312
        150 0.308 0.305 0.301 0.298 0.294 0.291 0.287 0.284 0.281 0.277
        160 0.274 0.271 0.268 0.267 0.262 0.259 0.256 0.253 0.251 0.248
        170 0.245 0.243 0.240 0.237 0.235 0.232 0.230 0.227 0.225 0.223
        180 0.220 0.218 0.216 0.214 0.211 0.209 0.207 0.205 0.203 0.201
        190 0.199 0.197 0.195 0.193 0.191 0.189 0.188 0.186 0.184 0.182
        200 0.180 0.179 0.177 0.175 0.174 0.172 0.171 0.169 0.167 0.166
        210 0.164 0.163 0.161 0.160 0.159 0.157 0.156 0.154 0.153 0.152
        220 0.150 0.149 0.148 0.146 0.145 0.144 0.143 0.141 0.140 0.139
        230 0.138 0.137 0.136 0.135 0.133 0.132 0.131 0.130 0.129 0.128
        240 0.127 0.126 0.125 0.124 0.123 0.122 0.121 0.120 0.119 0.118
        250 0.117
        """
    ),
    "Q355": _build_stability_table(
        """
        0 1.000 0.997 0.994 0.991 0.988 0.985 0.982 0.979 0.976 0.973
        10 0.971 0.968 0.965 0.962 0.959 0.956 0.952 0.949 0.946 0.943
        20 0.940 0.937 0.934 0.930 0.927 0.924 0.920 0.917 0.913 0.909
        30 0.906 0.902 0.898 0.894 0.890 0.886 0.882 0.878 0.874 0.870
        40 0.867 0.864 0.860 0.857 0.853 0.849 0.845 0.841 0.837 0.833
        50 0.829 0.824 0.819 0.815 0.810 0.805 0.800 0.794 0.789 0.783
        60 0.777 0.771 0.765 0.759 0.752 0.746 0.739 0.732 0.725 0.718
        70 0.710 0.703 0.695 0.688 0.680 0.672 0.664 0.656 0.648 0.640
        80 0.632 0.623 0.615 0.607 0.599 0.591 0.583 0.574 0.566 0.558
        90 0.550 0.542 0.535 0.527 0.519 0.512 0.504 0.497 0.489 0.482
        100 0.475 0.467 0.460 0.452 0.445 0.438 0.431 0.424 0.418 0.411
        110 0.405 0.398 0.392 0.386 0.380 0.375 0.369 0.363 0.358 0.352
        120 0.347 0.342 0.337 0.332 0.327 0.322 0.318 0.313 0.309 0.304
        130 0.300 0.296 0.292 0.288 0.284 0.280 0.276 0.272 0.269 0.265
        140 0.261 0.258 0.255 0.251 0.248 0.245 0.242 0.238 0.235 0.232
        150 0.229 0.227 0.224 0.221 0.218 0.216 0.213 0.210 0.208 0.205
        160 0.203 0.201 0.198 0.196 0.194 0.191 0.189 0.187 0.185 0.183
        170 0.181 0.179 0.177 0.175 0.173 0.171 0.169 0.167 0.165 0.163
        180 0.162 0.160 0.158 0.157 0.155 0.153 0.152 0.150 0.149 0.147
        190 0.146 0.144 0.143 0.141 0.140 0.138 0.137 0.136 0.134 0.133
        200 0.132 0.130 0.129 0.128 0.127 0.126 0.124 0.123 0.122 0.121
        210 0.120 0.119 0.118 0.116 0.115 0.114 0.113 0.112 0.111 0.110
        220 0.109 0.108 0.107 0.106 0.106 0.105 0.104 0.103 0.101 0.101
        230 0.100 0.099 0.098 0.098 0.097 0.096 0.095 0.094 0.094 0.093
        240 0.092 0.091 0.091 0.090 0.089 0.088 0.088 0.087 0.086 0.086
        250 0.085
        """
    ),
}

def _build_tube_properties(
    *,
    steel_grade: str,
    outer_diameter_mm: float,
    thickness_mm: float,
    allowable_stress_n_mm2: float,
) -> Dict[str, float | str]:
    """Build circular tube section properties from diameter and thickness."""
    inner_diameter_mm = outer_diameter_mm - 2 * thickness_mm
    area_mm2 = float(np.pi * (outer_diameter_mm**2 - inner_diameter_mm**2) / 4)
    section_inertia_mm4 = float(
        np.pi * (outer_diameter_mm**4 - inner_diameter_mm**4) / 64
    )
    radius_of_gyration_mm = float(np.sqrt(section_inertia_mm4 / area_mm2))
    w_section_mm3 = float(section_inertia_mm4 / (outer_diameter_mm / 2))
    line_weight_kn_m = float(area_mm2 * 1e-6 * 78.5)  # 钢材体积重取 78.5 kN/m³

    return {
        "steel_grade": steel_grade,
        "outer_diameter_mm": outer_diameter_mm,
        "thickness_mm": thickness_mm,
        "area_mm2": area_mm2,
        "section_inertia_mm4": section_inertia_mm4,
        "radius_of_gyration_mm": radius_of_gyration_mm,
        "w_section_mm3": w_section_mm3,
        "line_weight_kn_m": line_weight_kn_m,
        "allowable_stress_n_mm2": allowable_stress_n_mm2,
    }


def _normalize_tube_size_key(raw_spec: str) -> str:
    """Normalize tube size text/codes to the internal specification key."""
    compact = (
        str(raw_spec or "")
        .upper()
        .replace("Φ", "PHI")
        .replace("桅", "PHI")
        .replace("×", "X")
        .replace("脳", "X")
        .replace("*", "X")
        .replace("_", "")
        .replace(".", "")
        .replace(" ", "")
    )

    if any(token in compact for token in ("PHI48X325", "PHI483X325", "PHI48X32", "PHI483X32")):
        return "PHI48X3_25"
    if any(token in compact for token in ("PHI48X300", "PHI483X300", "PHI48X30", "PHI483X30")):
        return "PHI48X3_0"
    if any(token in compact for token in ("PHI48X275", "PHI483X275")):
        return "PHI48X2_75"

    raise ValueError(f"Unsupported tube size specification: {raw_spec}")


def _normalize_component_model_suffix(raw_model: str) -> str:
    """Normalize component model text and strip the B/Z prefix when present."""
    normalized_model = str(raw_model or "").strip().upper().replace("_", "-")
    if not normalized_model:
        return ""
    return normalized_model.split("-", 1)[-1]


def _format_context_value(value: Any) -> Any:
    """Recursively round numeric context values to at most 3 decimal places."""
    if isinstance(value, RichText):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value, 3) if value != round(value, 3) else value
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        numeric_value = float(value)
        return (
            round(numeric_value, 3)
            if numeric_value != round(numeric_value, 3)
            else numeric_value
        )
    if isinstance(value, dict):
        return {key: _format_context_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_format_context_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_format_context_value(item) for item in value)
    return value


def _make_result_rt(
    is_ok: bool,
    pass_text: str = "满足要求！",
    fail_text: str = "不满足要求！！！",
) -> RichText:
    """
    根据验算结果生成带颜色的 RichText 对象。

    满足要求：绿色（#00B050）
    不满足要求：红色（#FF0000）
    """
    if is_ok:
        return RichText(pass_text, color="00B050", bold=True, size=24)
    return RichText(fail_text, color="FF0000", bold=True, size=24)


_VERTICAL_TUBE_DISPLAY_NAMES = {
    "standard_b": "标准型（B型）Φ48.3×3.2",
    "heavy_z": "重型（Z型）Φ60.3×3.2",
}

_POLE_TUBE_DISPLAY_NAMES = {
    "standard_b": "Φ48.3×3.2",
    "heavy_z": "Φ60.3×3.2",
}

_VERTICAL_TUBE_PROPERTIES = {
    "standard_b": _build_tube_properties(
        steel_grade="Q355",
        outer_diameter_mm=48.3,  # 标准型（B型）盘扣立杆外径 D，JGJ/T 231-2021 表3.1.2
        thickness_mm=3.2,  # 标准型（B型）盘扣立杆壁厚 t，JGJ/T 231-2021 表3.1.2
        allowable_stress_n_mm2=310.0,  # Q355 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
    "heavy_z": _build_tube_properties(
        steel_grade="Q355",
        outer_diameter_mm=60.3,  # 重型（Z型）盘扣立杆外径 D，JGJ/T 231-2021 表3.1.2
        thickness_mm=3.2,  # 重型（Z型）盘扣立杆壁厚 t，JGJ/T 231-2021 表3.1.2
        allowable_stress_n_mm2=310.0,  # Q355 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
}

_BRACE_TUBE_DISPLAY_NAME = "Φ48.3×2.5"

_BRACE_TUBE_PROPERTIES = _build_tube_properties(
    steel_grade="Q355",
    outer_diameter_mm=48.3,  # 外斜杆截面固定外径 D，JGJ/T 231-2021 表3.1.2
    thickness_mm=2.5,  # 外斜杆截面固定壁厚 t，JGJ/T 231-2021 表3.1.2
    allowable_stress_n_mm2=310.0,  # Q355 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
)

_HORIZONTAL_TUBE_PROPERTIES = {
    "Q355_PHI48X3_25": _build_tube_properties(
        steel_grade="Q355",
        outer_diameter_mm=48.3,
        thickness_mm=3.25,
        allowable_stress_n_mm2=310.0,  # Q355 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
    "Q355_PHI48X3_0": _build_tube_properties(
        steel_grade="Q355",
        outer_diameter_mm=48.3,
        thickness_mm=3.0,
        allowable_stress_n_mm2=310.0,  # Q355 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
    "Q355_PHI48X2_75": _build_tube_properties(
        steel_grade="Q355",
        outer_diameter_mm=48.3,
        thickness_mm=2.75,
        allowable_stress_n_mm2=310.0,  # Q355 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
    "Q235_PHI48X3_25": _build_tube_properties(
        steel_grade="Q235",
        outer_diameter_mm=48.3,
        thickness_mm=3.25,
        allowable_stress_n_mm2=205.0,  # Q235 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
    "Q235_PHI48X2_75": _build_tube_properties(
        steel_grade="Q235",
        outer_diameter_mm=48.3,
        thickness_mm=2.75,
        allowable_stress_n_mm2=205.0,  # Q235 钢材抗压/抗弯强度设计值，JGJ/T 231-2021 表B.0.1
    ),
}

_WALL_TIE_TUBE_SPEC_DIMENSIONS = {
    "Φ48×3.25": (48.0, 3.25),
    "Φ48×2.75": (48.0, 2.75),
}

_CONCRETE_FC_TABLE = {
    "C20": 9.6,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
    "C25": 11.9,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
    "C30": 14.3,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
    "C35": 16.7,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
    "C40": 19.1,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
    "C45": 21.1,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
    "C50": 23.1,  # 混凝土轴心抗压强度设计值 fc，GB 50010-2010 表4.1.4
}


class ExteriorScaffoldCalculator(BaseCalculator):
    """盘扣式双排外脚手架计算器。"""

    def __init__(self) -> None:
        super().__init__()
        self._horizontal_ledger_result: Dict[str, Any] = {}
        self._vertical_standard_result: Dict[str, Any] = {}
        self._wall_tie_result: Dict[str, Any] = {}
        self._foundation_result: Dict[str, Any] = {}
        self.max_utilization_ratio: float = 0.0
        self.governing_check_item: Optional[str] = None

    def _update_max_utilization(self, check_item: str, ratio: float) -> None:
        """更新当前计算流程中的最大利用率与控制项。"""
        if ratio >= self.max_utilization_ratio:
            self.max_utilization_ratio = ratio
            self.governing_check_item = check_item

    def _get_vertical_tube_properties(self) -> Dict[str, float | str]:
        """Return section and material properties for the selected vertical tube."""
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法获取立杆截面参数。")

        spec = self.request_data.material_load_params.vertical_tube_spec
        pole_tube_spec = str(self.request_data.material_load_params.pole_tube_spec).strip()
        if spec not in _VERTICAL_TUBE_PROPERTIES:
            pole_model = str(self.request_data.material_load_params.pole_model).strip().upper()
            pole_suffix = _normalize_component_model_suffix(pole_model)
            normalized_pole_tube_spec = pole_tube_spec.upper().replace("Φ", "").replace("×", "X")
            if pole_suffix == "LG-300":
                normalized_spec = (
                    "heavy_z" if pole_model.startswith("Z-") else "standard_b"
                )
                return _VERTICAL_TUBE_PROPERTIES[normalized_spec]
            if normalized_pole_tube_spec.startswith("60.3X3.2"):
                return _VERTICAL_TUBE_PROPERTIES["heavy_z"]
            if normalized_pole_tube_spec.startswith("48.3X3.2"):
                return _VERTICAL_TUBE_PROPERTIES["standard_b"]
            raise ValueError(f"不支持的盘扣立杆类型: {spec}")
        return _VERTICAL_TUBE_PROPERTIES[spec]

    def _get_brace_tube_properties(self) -> Dict[str, float | str]:
        """Return fixed section and material properties for the diagonal brace tube."""
        return _BRACE_TUBE_PROPERTIES

    def _get_horizontal_tube_properties(self) -> Dict[str, float | str]:
        """Return section and material properties for the selected horizontal ledger."""
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法获取横杆截面参数。")

        ledger_model = str(self.request_data.material_load_params.ledger_model).strip().upper()
        ledger_suffix = _normalize_component_model_suffix(ledger_model)
        supported_ledger_suffixes = {"", "SG"}
        if ledger_suffix not in supported_ledger_suffixes:
            raise ValueError(f"不支持的横杆型号: {ledger_model}")

        spec = self.request_data.material_load_params.horizontal_tube_spec
        if spec not in _HORIZONTAL_TUBE_PROPERTIES:
            raise ValueError(f"不支持的横杆钢管规格: {spec}")
        return _HORIZONTAL_TUBE_PROPERTIES[spec]

    def _normalize_wall_tie_connection_type(self, raw_value: str) -> str:
        """Normalize legacy/new wall tie connection type values."""
        normalized_value = str(raw_value or "").strip()
        legacy_mapping = {
            "EXPANSION_BOLT": "anchor_bolt",
            "CHEMICAL_BOLT": "anchor_bolt",
            "EMBEDDED": "embedded_tube",
        }
        return legacy_mapping.get(normalized_value, normalized_value or "anchor_bolt")

    def _normalize_wall_tie_fastener_type(self, raw_value: str) -> str:
        """Normalize legacy/new fastener values to Chinese labels."""
        normalized_value = str(raw_value or "").strip()
        fastener_mapping = {
            "DOUBLE": "双扣件",
            "SINGLE": "单扣件",
        }
        return fastener_mapping.get(normalized_value, normalized_value or "双扣件")

    def _get_phi(self, lambda_val: float, steel_grade: str = "Q355") -> float:
        """Compatibility wrapper for the appendix-C stability factor lookup."""
        return self._get_stability_factor(lambda_val, steel_grade)

    def _get_concrete_fc(self, concrete_grade: str) -> float:
        """Return the concrete axial compressive design strength fc."""
        normalized_grade = str(concrete_grade or "").strip().upper()
        if normalized_grade not in _CONCRETE_FC_TABLE:
            raise ValueError(f"不支持的混凝土强度等级: {concrete_grade}")
        return _CONCRETE_FC_TABLE[normalized_grade]

    def _get_wall_tie_tube_properties(self, tube_spec: str) -> Dict[str, float | str]:
        """Return section and material properties for the selected wall tie tube."""
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法获取连墙件截面参数。")

        normalized_spec = str(tube_spec or "").strip().replace("x", "×").replace("X", "×")
        legacy_spec_mapping = {
            "Φ48×3.2": "Φ48×3.25",
            "Φ48.3×3.2": "Φ48×3.25",
            "Φ48.3×3.25": "Φ48×3.25",
            "Φ48.3×2.75": "Φ48×2.75",
        }
        normalized_spec = legacy_spec_mapping.get(normalized_spec, normalized_spec)
        if normalized_spec not in _WALL_TIE_TUBE_SPEC_DIMENSIONS:
            raise ValueError(f"不支持的连墙件钢管规格: {tube_spec}")

        outer_diameter_mm, thickness_mm = _WALL_TIE_TUBE_SPEC_DIMENSIONS[normalized_spec]
        steel_grade = str(self._get_vertical_tube_properties()["steel_grade"])
        allowable_stress = (
            205.0 if steel_grade == "Q235" else 310.0
        )  # Q235/Q355 钢材抗拉、抗压、抗弯强度设计值，JGJ/T 231-2021 表B.0.1
        tube_props = _build_tube_properties(
            steel_grade=steel_grade,
            outer_diameter_mm=outer_diameter_mm,  # 连墙件钢管名义外径 D=48mm，本次业务需求约定规格 Φ48×t
            thickness_mm=thickness_mm,  # 连墙件钢管壁厚 t，按规格 Φ48×3.25 / Φ48×2.75 取值
            allowable_stress_n_mm2=allowable_stress,
        )
        tube_props["tube_spec"] = normalized_spec
        return tube_props

    def _get_stability_factor(
        self, lambda_val: float, steel_grade: str = "Q355"
    ) -> float:
        """根据 JGJ/T 231-2021 附录 C 查表并线性插值获取稳定系数 φ。"""
        if steel_grade not in _STABILITY_FACTOR_TABLES:
            raise ValueError(f"不支持的钢材牌号: {steel_grade}")

        table = _STABILITY_FACTOR_TABLES[steel_grade]
        min_lambda = 0
        max_lambda = len(table) - 1
        clamped_lambda = max(float(min_lambda), min(float(lambda_val), float(max_lambda)))
        lower_lambda = int(clamped_lambda)

        if lower_lambda >= max_lambda or clamped_lambda == lower_lambda:
            return float(table[lower_lambda])

        upper_lambda = lower_lambda + 1
        lower_phi = float(table[lower_lambda])
        upper_phi = float(table[upper_lambda])
        ratio = clamped_lambda - lower_lambda
        return lower_phi + (upper_phi - lower_phi) * ratio

    def _check_horizontal_ledger(self) -> Dict[str, Any]:
        """
        横向横杆验算。

        横向横杆验算（商用级重构版）。

        计算逻辑对应真实计算书：
        1. 提取单块脚手板宽度 b、爪钩数量 j、脚手板自重 Gkjb、施工活荷载 Qkjj
        2. 承载能力极限状态：计算设计线荷载 q、支座反力 R、跨中最大弯矩 Mmax、抗弯应力 σ
        3. 正常使用极限状态：计算标准组合线荷载 q' 和最大挠度 vmax
        4. 节点抗剪验算：F_R = γ0 × R1 ≤ 40kN
        """
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行横向横杆验算。")

        # -----------------------------
        # 1) 提取输入参数
        # -----------------------------
        la = self.request_data.geometry_params.longitudinal_spacing_la_m
        lb = self.request_data.geometry_params.transverse_spacing_lb_m
        gamma_0 = self.request_data.basic_info.importance_factor

        # 单块脚手板宽度 b，由 mm 转换为 m
        b = self.request_data.material_load_params.single_plank_width_b_mm / 1000
        j = self.request_data.material_load_params.hook_count_per_side_j
        gkjb = self.request_data.material_load_params.plank_self_weight_kn_m2
        qkjj = self.request_data.material_load_params.construction_live_load_kn_m2

        # -----------------------------
        # 2) 常量与截面参数
        # -----------------------------
        q1_k = 0.028  # 横杆自重线荷载标准值，kN/m；Φ48.3×3.0横杆理论线重量，kN/m
        w_section = 3920.0  # 横杆截面抵抗矩 W，mm³；Φ48.3×3.0横杆截面模量W，mm³
        allowable_stress = 205.0  # 抗弯强度设计值 [f]，N/mm²；Q235钢抗弯强度设计值，N/mm²，附录B.0.1
        elastic_modulus = 206000.0  # N/mm^2
        section_inertia = w_section * 24.0  # mm^4；I=W×c，c=24mm为Φ48.3管外壁到中性轴距离，mm⁴

        # -----------------------------
        # 3) 承载能力极限状态
        # -----------------------------
        # 设计线荷载 q = b × (1.3 × Gkjb + 1.5 × Qkjj)
        line_load_design = b * (1.3 * gkjb + 1.5 * qkjj)  # kN/m；1.3、1.5为永久/可变荷载分项系数γG、γQ，见规范表4.3.1
        # 支座反力 R = q × la / j（单个爪钩或单侧分配反力）
        support_reaction_component = line_load_design * la / j  # kN
        # 横杆自重设计值 q1 = 1.3 × q1_k
        self_weight_design = 1.3 * q1_k  # kN/m；1.3为永久荷载分项系数γG，见规范表4.3.1

        # -----------------------------
        # 4) 简支梁内力计算
        # -----------------------------
        # 跨中最大弯矩：
        # Mmax = q1 × lb² / 8 + (R × j) × lb / 4
        concentrated_load_design_total = support_reaction_component * j  # kN
        max_bending_moment = (
            self_weight_design * lb**2 / 8
            + concentrated_load_design_total * lb / 4
        )  # kN·m

        # 支座最大反力设计值 R1，用于节点抗剪验算
        support_reaction_design = (
            self_weight_design * lb / 2 + concentrated_load_design_total / 2
        )  # kN

        # -----------------------------
        # 5) 抗弯验算
        # -----------------------------
        # σ = Mmax × 10^6 / W
        sigma = max_bending_moment * 1_000_000 / w_section  # N/mm²
        bending_ratio = sigma / allowable_stress if allowable_stress else 0.0
        bending_passed = sigma <= allowable_stress

        # -----------------------------
        # 6) 正常使用极限状态：挠度验算
        # -----------------------------
        # 标准组合线荷载 q' = b × (Gkjb + Qkjj)
        line_load_standard = b * (gkjb + qkjj)  # kN/m
        support_reaction_standard_component = line_load_standard * la / j  # kN
        concentrated_load_standard_total = support_reaction_standard_component * j  # kN

        # 采用“横杆自重标准值 + 跨中集中力标准值”的简化梁模型计算最大挠度
        lb_mm = lb * 1000
        q_standard_total_n_per_mm = q1_k + line_load_standard  # 1kN/m = 1N/mm
        concentrated_load_standard_n = concentrated_load_standard_total * 1000  # N
        max_deflection = (
            5 * q_standard_total_n_per_mm * lb_mm**4
            / (384 * elastic_modulus * section_inertia)
            + concentrated_load_standard_n * lb_mm**3
            / (48 * elastic_modulus * section_inertia)
        )  # mm
        deflection_limit = min(lb_mm / 150, 10.0)  # mm；l/150且不大于10mm为受弯构件容许挠度限值，见规范表5.1.5
        deflection_ratio = (
            max_deflection / deflection_limit if deflection_limit else 0.0
        )
        deflection_passed = max_deflection <= deflection_limit

        # -----------------------------
        # 7) 盘扣节点抗剪验算
        # -----------------------------
        # 节点受剪力设计值 F_R = γ0 × R1
        node_shear_design = gamma_0 * support_reaction_design  # kN
        shear_limit = 40.0  # kN；盘扣节点连接盘受剪承载力设计值Qb，kN，见规范第5.5.1条
        shear_ratio = node_shear_design / shear_limit if shear_limit else 0.0
        shear_passed = node_shear_design <= shear_limit

        # -----------------------------
        # 6) 记录不通过项
        # -----------------------------
        if not bending_passed:
            self.issues.append(
                IssueItem(
                    item_code="HORIZONTAL_LEDGER_BENDING_EXCEEDED",
                    check_item="横向横杆抗弯验算",
                    field_path="geometry_params.transverse_spacing_lb_m",
                    current_value=round(sigma, 3),
                    limit_value=allowable_stress,
                    severity="error",
                    message=(
                        f"横向横杆抗弯应力为 {sigma:.3f} N/mm²，"
                        f"已超过允许值 {allowable_stress:.3f} N/mm²。"
                    ),
                    suggestion="建议减小立杆横距 lb、降低施工活荷载，或提高横杆截面承载能力。",
                )
            )

        if not deflection_passed:
            self.issues.append(
                IssueItem(
                    item_code="HORIZONTAL_LEDGER_DEFLECTION_EXCEEDED",
                    check_item="横向横杆挠度验算",
                    field_path="geometry_params.transverse_spacing_lb_m",
                    current_value=round(max_deflection, 3),
                    limit_value=round(deflection_limit, 3),
                    severity="error",
                    message=(
                        f"横向横杆最大挠度为 {max_deflection:.3f} mm，"
                        f"已超过限值 {deflection_limit:.3f} mm。"
                    ),
                    suggestion="建议减小横杆跨度、降低作业荷载，或增大横杆刚度。",
                )
            )

        if not shear_passed:
            self.issues.append(
                IssueItem(
                    item_code="HORIZONTAL_LEDGER_SHEAR_EXCEEDED",
                    check_item="盘扣节点抗剪验算",
                    field_path="material_load_params.construction_live_load_kn_m2",
                    current_value=round(node_shear_design, 3),
                    limit_value=shear_limit,
                    severity="error",
                    message=(
                        f"盘扣节点受剪力设计值为 {node_shear_design:.3f} kN，"
                        f"已超过允许值 {shear_limit:.3f} kN。"
                    ),
                    suggestion="建议降低施工活荷载，或优化脚手板布置与节点受力路径。",
                )
            )

        utilization_map = {
            "横向横杆抗弯验算": bending_ratio,
            "横向横杆挠度验算": deflection_ratio,
            "盘扣节点抗剪验算": shear_ratio,
        }
        governing_check_item = max(utilization_map, key=utilization_map.get)
        self._update_max_utilization(
            governing_check_item, utilization_map[governing_check_item]
        )

        result = {
            "la_m": la,
            "lb_m": lb,
            "plank_width_m": b,
            "hook_count_per_side": j,
            "gkjb_kn_m2": gkjb,
            "qkjj_kn_m2": qkjj,
            "line_load_design_kn_m": line_load_design,
            "line_load_standard_kn_m": line_load_standard,
            "hook_reaction_design_k": support_reaction_component,
            "hook_reaction_standard_k": support_reaction_standard_component,
            "concentrated_load_standard_k": concentrated_load_standard_total,
            "concentrated_load_design_k": concentrated_load_design_total,
            "self_weight_design_kn_m": self_weight_design,
            "max_bending_moment_kn_m": max_bending_moment,
            "max_support_reaction_kn": support_reaction_design,
            "sigma_n_mm2": sigma,
            "allowable_stress_n_mm2": allowable_stress,
            "max_deflection_mm": max_deflection,
            "deflection_limit_mm": deflection_limit,
            "node_shear_design_kn": node_shear_design,
            "node_shear_limit_kn": shear_limit,
            "bending_ratio": bending_ratio,
            "deflection_ratio": deflection_ratio,
            "shear_ratio": shear_ratio,
            "governing_check_item": governing_check_item,
            "overall_passed": bending_passed and deflection_passed and shear_passed,
        }
        self._horizontal_ledger_result = result
        return result

    def _check_horizontal_ledger(self) -> Dict[str, Any]:
        """Horizontal ledger bending / deflection / node shear check."""
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行横向横杆验算。")

        la = self.request_data.geometry_params.longitudinal_spacing_la_m
        lb = self.request_data.geometry_params.transverse_spacing_lb_m
        gamma_0 = self.request_data.basic_info.importance_factor
        b = self.request_data.material_load_params.single_plank_width_b_mm / 1000
        j = self.request_data.material_load_params.hook_count_per_side_j
        gkjb = self.request_data.material_load_params.plank_self_weight_kn_m2
        qkjj = self.request_data.material_load_params.construction_live_load_kn_m2

        horizontal_tube_props = self._get_horizontal_tube_properties()
        q1_k = float(horizontal_tube_props["line_weight_kn_m"])  # 横杆自重标准值由所选钢管截面自重换算得到，kN/m
        w_section = float(horizontal_tube_props["w_section_mm3"])  # 横杆截面模量 W，mm³
        allowable_stress = float(horizontal_tube_props["allowable_stress_n_mm2"])  # 钢管抗弯强度设计值 [f]，JGJ/T 231-2021 表B.0.1
        elastic_modulus = 206000.0  # 钢材弹性模量 E，N/mm²
        section_inertia = float(horizontal_tube_props["section_inertia_mm4"])  # 横杆截面惯性矩 I，mm⁴

        line_load_design = b * (1.3 * gkjb + 1.5 * qkjj)  # 永久/可变荷载分项系数按 JGJ/T 231-2021 表5.3.1
        support_reaction_component = line_load_design * la / j
        self_weight_design = 1.3 * q1_k  # 永久荷载分项系数按 JGJ/T 231-2021 表5.3.1

        concentrated_load_design_total = support_reaction_component * j
        max_bending_moment = (
            self_weight_design * lb**2 / 8 + concentrated_load_design_total * lb / 4
        )
        support_reaction_design = (
            self_weight_design * lb / 2 + concentrated_load_design_total / 2
        )

        sigma = max_bending_moment * 1_000_000 / w_section
        bending_ratio = sigma / allowable_stress if allowable_stress else 0.0
        bending_passed = sigma <= allowable_stress

        line_load_standard = b * (gkjb + qkjj)
        support_reaction_standard_component = line_load_standard * la / j
        concentrated_load_standard_total = support_reaction_standard_component * j

        lb_mm = lb * 1000
        q_standard_total_n_per_mm = q1_k + line_load_standard
        concentrated_load_standard_n = concentrated_load_standard_total * 1000
        max_deflection = (
            5 * q_standard_total_n_per_mm * lb_mm**4
            / (384 * elastic_modulus * section_inertia)
            + concentrated_load_standard_n * lb_mm**3
            / (48 * elastic_modulus * section_inertia)
        )
        deflection_limit = lb_mm / 150  # 受弯构件挠度限值取 L/150
        deflection_ratio = (
            max_deflection / deflection_limit if deflection_limit else 0.0
        )
        deflection_passed = max_deflection <= deflection_limit

        node_shear_design = gamma_0 * support_reaction_design
        shear_limit = 40.0  # 盘扣节点抗剪承载力设计值，JGJ/T 231-2021 第5.5.1条
        shear_ratio = node_shear_design / shear_limit if shear_limit else 0.0
        shear_passed = node_shear_design <= shear_limit

        if not bending_passed:
            self.issues.append(
                IssueItem(
                    item_code="HORIZONTAL_LEDGER_BENDING_EXCEEDED",
                    check_item="横向横杆抗弯验算",
                    field_path="material_load_params.horizontal_tube_spec",
                    current_value=round(sigma, 3),
                    limit_value=round(allowable_stress, 3),
                    severity="error",
                    message=(
                        f"横向横杆抗弯应力为 {sigma:.3f} N/mm²，"
                        f"已超过允许值 {allowable_stress:.3f} N/mm²。"
                    ),
                    suggestion="建议增大横杆壁厚、减小横距 lb，或降低施工活荷载。",
                )
            )

        if not deflection_passed:
            self.issues.append(
                IssueItem(
                    item_code="HORIZONTAL_LEDGER_DEFLECTION_EXCEEDED",
                    check_item="横向横杆挠度验算",
                    field_path="geometry_params.transverse_spacing_lb_m",
                    current_value=round(max_deflection, 3),
                    limit_value=round(deflection_limit, 3),
                    severity="error",
                    message=(
                        f"横向横杆最大挠度为 {max_deflection:.3f} mm，"
                        f"已超过限值 {deflection_limit:.3f} mm。"
                    ),
                    suggestion="建议增大横杆刚度、减小横距 lb，或降低施工活荷载。",
                )
            )

        if not shear_passed:
            self.issues.append(
                IssueItem(
                    item_code="HORIZONTAL_LEDGER_SHEAR_EXCEEDED",
                    check_item="盘扣节点抗剪验算",
                    field_path="material_load_params.construction_live_load_kn_m2",
                    current_value=round(node_shear_design, 3),
                    limit_value=round(shear_limit, 3),
                    severity="error",
                    message=(
                        f"盘扣节点受剪设计值为 {node_shear_design:.3f} kN，"
                        f"已超过允许值 {shear_limit:.3f} kN。"
                    ),
                    suggestion="建议降低施工活荷载，或优化脚手板布置与节点受力路径。",
                )
            )

        utilization_map = {
            "横向横杆抗弯验算": bending_ratio,
            "横向横杆挠度验算": deflection_ratio,
            "盘扣节点抗剪验算": shear_ratio,
        }
        governing_check_item = max(utilization_map, key=utilization_map.get)
        self._update_max_utilization(
            governing_check_item, utilization_map[governing_check_item]
        )

        result = {
            "la_m": la,
            "lb_m": lb,
            "plank_width_m": b,
            "hook_count_per_side": j,
            "tube_spec": self.request_data.material_load_params.horizontal_tube_spec,
            "tube_outer_diameter_mm": float(horizontal_tube_props["outer_diameter_mm"]),
            "tube_thickness_mm": float(horizontal_tube_props["thickness_mm"]),
            "tube_area_mm2": float(horizontal_tube_props["area_mm2"]),
            "tube_section_inertia_mm4": section_inertia,
            "gkjb_kn_m2": gkjb,
            "qkjj_kn_m2": qkjj,
            "line_load_design_kn_m": line_load_design,
            "line_load_standard_kn_m": line_load_standard,
            "hook_reaction_design_k": support_reaction_component,
            "hook_reaction_standard_k": support_reaction_standard_component,
            "concentrated_load_standard_k": concentrated_load_standard_total,
            "concentrated_load_design_k": concentrated_load_design_total,
            "self_weight_design_kn_m": self_weight_design,
            "self_weight_standard_kn_m": q1_k,
            "max_bending_moment_kn_m": max_bending_moment,
            "max_support_reaction_kn": support_reaction_design,
            "sigma_n_mm2": sigma,
            "allowable_stress_n_mm2": allowable_stress,
            "allowable_stress_mpa": allowable_stress,
            "max_deflection_mm": max_deflection,
            "deflection_limit_mm": deflection_limit,
            "node_shear_design_kn": node_shear_design,
            "node_shear_limit_kn": shear_limit,
            "bending_check": bending_passed,
            "deflection_check": deflection_passed,
            "shear_check": shear_passed,
            "bending_ratio": bending_ratio,
            "deflection_ratio": deflection_ratio,
            "shear_ratio": shear_ratio,
            "bending_result_rt": _make_result_rt(bending_passed),
            "deflection_result_rt": _make_result_rt(deflection_passed),
            "shear_result_rt": _make_result_rt(shear_passed),
            "governing_check_item": governing_check_item,
            "overall_passed": bending_passed and deflection_passed and shear_passed,
        }
        self._horizontal_ledger_result = result
        return result

    def _check_vertical_standard(self) -> Dict[str, Any]:
        """
        立杆稳定性验算。

        立杆稳定性验算（商用级双轨制）。

        计算逻辑：
        1. 基于真实计算书区分内排与外排立杆
        2. 结构自重 NG1k 按内外排分别统计
        3. 构配件自重 NG2k 按偏心分配差异统计
        4. 活荷载 NQ1k 由作业层数和施工活荷载计算
        5. 轴向力分别计算 N1、N2，取最不利轴力 design N
        6. 计算 wk、Mw、长细比 λ、稳定系数 φ、组合压应力 σ
        """
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行立杆稳定性验算。")

        # -----------------------------
        # 1) 参数准备
        # -----------------------------
        hs = self.request_data.geometry_params.erection_height_hs_m
        la = self.request_data.geometry_params.longitudinal_spacing_la_m
        lb = self.request_data.geometry_params.transverse_spacing_lb_m
        h = self.request_data.geometry_params.step_height_h_m
        h1 = self.request_data.geometry_params.guardrail_top_height_h1_m
        h2_mm = self.request_data.geometry_params.sweeping_rod_height_h2_mm
        tie_member_layout = self.request_data.wall_tie_params.layout
        working_layer_count = self.request_data.material_load_params.working_layer_count
        qkjj = (
            self.request_data.material_load_params.construction_live_load_kn_m2
        )
        plank_self_weight = self.request_data.material_load_params.plank_self_weight_kn_m2
        gamma_0 = self.request_data.basic_info.importance_factor

        tube_props = self._get_vertical_tube_properties()
        steel_grade = str(tube_props["steel_grade"])
        area = float(tube_props["area_mm2"])  # A，mm²
        radius_of_gyration = float(tube_props["radius_of_gyration_mm"])  # mm
        w_section = float(tube_props["w_section_mm3"])  # W，mm³
        allowable_stress = float(tube_props["allowable_stress_n_mm2"])  # [f]，N/mm²

        # 系统常量（真实计算书简化映射）
        gkdb = 0.17  # 挡脚板线荷载，kN/m；栏杆与挡脚板自重标准值，见 JGJ/T 231-2021 第4.2.2条第3款
        gkmw = 0.01  # 安全网面荷载，kN/㎡；密目式安全网自重标准值，见 JGJ/T 231-2021 第4.2.2条第4款
        m1 = float(tube_props["line_weight_kn_m"])  # 立杆单位长度自重，由所选盘扣立杆类型截面面积按钢材容重换算
        m2 = 0.050  # 纵向横杆单重；纵向水平杆单位长度自重，kN/m
        m3 = 0.033  # 横向横杆单重；横向水平杆单位长度自重，kN/m
        brace_props = self._get_brace_tube_properties()
        m4 = float(brace_props["line_weight_kn_m"])  # 外斜杆单位长度自重，按Φ48.3×2.5截面面积和钢材容重换算

        w0 = self.request_data.material_load_params.basic_wind_pressure_w0_kn_m2
        muz = self.request_data.material_load_params.wind_height_factor_muz
        us = self.request_data.material_load_params.wind_shape_factor

        # 计算有效步数 n = int((Hs - h1 - h2/1000) / h)
        n = max(1, int((hs - h1 - h2_mm / 1000) / h))

        # 连墙件布置方式对应的计算长度系数 μ
        mu_map = {
            "ONE_STEP_TWO_SPAN": 1.45,
            "TWO_STEP_TWO_SPAN": 1.45,
            "TWO_STEP_THREE_SPAN": 1.45,
            "THREE_STEP_THREE_SPAN": 1.70,
        }
        mu = mu_map.get(tie_member_layout, 1.45)

        # -----------------------------
        # 2) 荷载累加：计算 NG1k、NG2k、NQ1k
        # -----------------------------
        # 内排立杆结构自重：
        # NG1k_inner = (m1×Hs/3) + m2×(n+1) + m3×(n+1)/2
        ng1k_inner = (m1 * hs / 3) + m2 * (n + 1) + m3 * (n + 1) / 2

        # 外排立杆结构自重：
        # NG1k_outer = NG1k_inner + m4×n/2
        ng1k_outer = ng1k_inner + m4 * n / 2

        # 内排立杆构配件自重：
        # NG2k_inner = (n+1) × la × lb × Gkjb / 2
        ng2k_inner = (n + 1) * la * lb * plank_self_weight / 2

        # 外排立杆构配件自重：
        # NG2k_outer = NG2k_inner + (n+1)×la×Gkdb + Gkmw×la×Hs
        ng2k_outer = ng2k_inner + (n + 1) * la * gkdb + gkmw * la * hs

        # 活荷载：
        # NQ1k = la × lb × (njj × Qkjj) / 2
        nq1k = la * lb * (working_layer_count * qkjj) / 2

        # 轴向力设计值分别计算内排与外排
        n1_no_wind = 1.3 * (ng1k_inner + ng2k_inner) + 1.5 * nq1k  # 1.3、1.5为永久/可变荷载分项系数γG、γQ，见规范表4.3.1
        n2_no_wind = 1.3 * (ng1k_outer + ng2k_outer) + 1.5 * nq1k  # 1.3、1.5为永久/可变荷载分项系数γG、γQ，见规范表4.3.1
        n1_with_wind = 1.3 * (ng1k_inner + ng2k_inner) + 0.9 * 1.5 * nq1k  # 0.9为有风组合系数，见规范第5.4.2条式(5.4.2-1)；1.5为可变荷载分项系数γQ
        n2_with_wind = 1.3 * (ng1k_outer + ng2k_outer) + 0.9 * 1.5 * nq1k  # 0.9为有风组合系数，见规范第5.4.2条式(5.4.2-1)；1.5为可变荷载分项系数γQ
        axial_force_no_wind_kn = max(n1_no_wind, n2_no_wind)
        axial_force_with_wind_kn = max(n1_with_wind, n2_with_wind)
        axial_force_design_kn = max(axial_force_no_wind_kn, axial_force_with_wind_kn)

        # -----------------------------
        # 3) 长细比验算
        # -----------------------------
        effective_length_m = mu * h  # m
        lambda_geometric = h * 1000 / radius_of_gyration
        lambda_calc = effective_length_m * 1000 / radius_of_gyration
        lambda_val = lambda_calc
        lambda_limit = 210.0  # 作业架立杆几何长细比限值，见规范第5.1.6条
        lambda_ratio = lambda_geometric / lambda_limit if lambda_limit else 0.0
        slenderness_passed = lambda_geometric <= lambda_limit

        if not slenderness_passed:
            self.issues.append(
                IssueItem(
                    item_code="VERTICAL_STANDARD_SLENDERNESS_EXCEEDED",
                    check_item="立杆长细比验算",
                    field_path="geometry_params.step_height_h_m",
                    current_value=round(lambda_geometric, 3),
                    limit_value=lambda_limit,
                    severity="error",
                    message=(
                        f"立杆几何长细比为 {lambda_geometric:.3f}，"
                        f"已超过限值 {lambda_limit:.3f}。"
                    ),
                    suggestion="建议减小步距 h、选用更大回转半径的立杆，或降低架体搭设高度。",
                )
            )

        self._update_max_utilization("立杆长细比验算", lambda_ratio)
        phi = self._get_stability_factor(lambda_calc, steel_grade)

        # -----------------------------
        # 4) 风荷载弯矩计算
        # -----------------------------
        # wk = w0 × μz × us
        wk = w0 * muz * us
        # Mw = 0.9 × 1.5 × wk × la × h² / 10
        mw = 0.9 * 1.5 * wk * la * (h**2) / 10  # kN·m；0.9为有风组合系数，1.5为风荷载分项系数，见规范第5.4.2条式(5.4.2-1)

        # -----------------------------
        # 5) 稳定性组合应力验算
        # -----------------------------
        # 无风：σ = N/(φA)
        sigma_no_wind = (axial_force_no_wind_kn * 1000) / (phi * area)  # N/mm²
        # 有风：σ = N/(φA) + Mw/W
        sigma_with_wind = (
            (axial_force_with_wind_kn * 1000) / (phi * area)
            + (mw * 1_000_000) / w_section
        )  # N/mm²
        sigma = max(sigma_no_wind, sigma_with_wind)
        stability_ratio = sigma / allowable_stress if allowable_stress else 0.0
        stability_passed = sigma <= allowable_stress

        if not stability_passed:
            self.issues.append(
                IssueItem(
                    item_code="VERTICAL_STANDARD_STABILITY_EXCEEDED",
                    check_item="立杆稳定性验算",
                    field_path="geometry_params.step_height_h_m",
                    current_value=round(sigma, 3),
                    limit_value=allowable_stress,
                    severity="error",
                    message=(
                        f"立杆组合应力为 {sigma:.3f} N/mm²，"
                        f"已超过允许值 {allowable_stress:.3f} N/mm²，立杆稳定性验算不通过。"
                    ),
                    suggestion="建议减小步距、加密连墙件、降低搭设高度或降低作业荷载。",
                )
            )

        self._update_max_utilization("立杆稳定性验算", stability_ratio)

        result = {
            "hs_m": hs,
            "la_m": la,
            "lb_m": lb,
            "h_m": h,
            "step_count_n": n,
            "mu": mu,
            "mu_desc": {
                "ONE_STEP_TWO_SPAN": "一步两跨",
                "TWO_STEP_TWO_SPAN": "两步两跨",
                "TWO_STEP_THREE_SPAN": "两步三跨",
                "THREE_STEP_THREE_SPAN": "三步三跨",
            }.get(tie_member_layout, "一步两跨"),
            "m1_kn": m1,
            "m2_kn": m2,
            "m3_kn": m3,
            "m4_kn": m4,
            "wk_kn_m2": wk,
            "muz": muz,
            "area_mm2": area,
            "radius_of_gyration_mm": radius_of_gyration,
            "w_section_mm3": w_section,
            "allowable_stress_n_mm2": allowable_stress,
            "gamma_0": gamma_0,
            "ng1k1_kn": m1 * hs / 3,
            "ng1k_inner_kn": ng1k_inner,
            "ng1k_outer_kn": ng1k_outer,
            "ng1k2_inner_kn": m2 * (n + 1),
            "ng1k3_kn": m3 * (n + 1) / 2,
            "ng1k4_kn": m4 * n / 2,
            "ng2k_inner_kn": ng2k_inner,
            "ng2k_outer_kn": ng2k_outer,
            "ng2k2_kn": (n + 1) * la * gkdb,
            "ng2k3_kn": gkmw * la * hs,
            "ng1k_kn": ng1k_outer,
            "ng2k_kn": ng2k_outer,
            "nq1k_kn": nq1k,
            "n1_kn": n1_with_wind,
            "n2_kn": n2_with_wind,
            "n1_no_wind_kn": n1_no_wind,
            "n2_no_wind_kn": n2_no_wind,
            "n1_with_wind_kn": n1_with_wind,
            "n2_with_wind_kn": n2_with_wind,
            "axial_force_no_wind_kn": axial_force_no_wind_kn,
            "axial_force_with_wind_kn": axial_force_with_wind_kn,
            "axial_force_design_kn": axial_force_design_kn,
            "effective_length_m": effective_length_m,
            "lambda_geometric": lambda_geometric,
            "lambda_calc": lambda_calc,
            "lambda_val": lambda_val,
            "lambda_limit": lambda_limit,
            "steel_grade": steel_grade,
            "phi": phi,
            "wind_bending_moment_kn_m": mw,
            "sigma_no_wind_n_mm2": sigma_no_wind,
            "sigma_no_wind": sigma_no_wind,
            "sigma_with_wind_n_mm2": sigma_with_wind,
            "sigma_with_wind": sigma_with_wind,
            "sigma_n_mm2": sigma,
            "lambda_check": slenderness_passed,
            "stability_check": stability_passed,
            "stability_ratio": stability_ratio,
            "lambda_ratio": lambda_ratio,
            "lambda_result_rt": _make_result_rt(slenderness_passed),
            "stability_result_rt": _make_result_rt(stability_passed),
            "governing_check_item": (
                "立杆长细比验算"
                if lambda_ratio >= stability_ratio
                else "立杆稳定性验算"
            ),
            "overall_passed": slenderness_passed and stability_passed,
        }
        self._vertical_standard_result = result
        return result

    def _check_wall_tie(self) -> Dict[str, Any]:
        """
        连墙件承载力验算。

        连墙件承载力验算（商用级重构版）。

        计算逻辑：
        1. 顶层连墙件按风压标准值 wk 计算迎风荷载
        2. 根据布置方式计算迎风面积 Aw
        3. 计算 Nlw = 1.5 × wk × Aw，Nt = Nlw + 3.0
        4. 执行杆件压应力、螺栓抗拔深度、螺栓抗拉、混凝土局部承压、扣件抗滑移五大验算
        """
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行连墙件验算。")

        # -----------------------------
        # 1) 提取参数
        # -----------------------------
        la = self.request_data.geometry_params.longitudinal_spacing_la_m
        h = self.request_data.geometry_params.step_height_h_m
        tie_member_layout = self.request_data.wall_tie_params.layout
        bolt_diameter_mm = self.request_data.wall_tie_params.bolt_diameter_d_mm
        bolt_tensile_strength = (
            self.request_data.wall_tie_params.bolt_tensile_strength_n_mm2
        )
        tau_b = self.request_data.wall_tie_params.allowable_bond_strength_n_mm2
        concrete_grade = self.request_data.wall_tie_params.concrete_grade
        fastener_connection_type = (
            self.request_data.wall_tie_params.fastener_connection_type
        )

        # 风荷载标准值：wk = w0 × μz × us
        w0 = self.request_data.material_load_params.basic_wind_pressure_w0_kn_m2
        muz = self.request_data.material_load_params.wind_height_factor_muz
        us = self.request_data.material_load_params.wind_shape_factor
        # 连墙件通常控制于顶层，当前取与立杆一致的风荷载标准值逻辑
        wk = w0 * muz * us

        # 连墙件杆件参数
        tube_props = self._get_vertical_tube_properties()
        steel_grade = str(tube_props["steel_grade"])
        area_c = float(tube_props["area_mm2"])  # Ac，mm²
        allowable_stress = float(tube_props["allowable_stress_n_mm2"])  # [f]，N/mm²
        i_tie_mm = float(tube_props["radius_of_gyration_mm"])
        inner_to_wall_m = self.request_data.geometry_params.inner_pole_to_wall_m
        l0_tie_mm = max(inner_to_wall_m * 1000, 300.0)  # 连墙件计算长度构造最小值300mm
        lambda_tie = l0_tie_mm / i_tie_mm
        phi = self._get_stability_factor(lambda_tie, steel_grade)
        n0 = 3.0  # 平面外变形附加轴向力 N0，kN；连墙件约束架体平面外变形轴向力N0，双排架取3kN，见规范第5.4.3条第1款

        # 扣件抗滑移承载力设计值：单扣件 8.0kN，双扣件 16.0kN
        slip_resistance = 16.0 if fastener_connection_type == "DOUBLE" else 8.0  # 双扣件/单扣件抗滑移承载力设计值Rc，kN，见规范第5.4.3条第4款

        # -----------------------------
        # 2) 连墙件轴向力计算
        # -----------------------------
        if tie_member_layout == "ONE_STEP_TWO_SPAN":
            aw = 1 * h * 2 * la
        elif tie_member_layout == "TWO_STEP_TWO_SPAN":
            aw = 2 * h * 2 * la
        elif tie_member_layout == "TWO_STEP_THREE_SPAN":
            aw = 2 * h * 3 * la
        elif tie_member_layout == "THREE_STEP_THREE_SPAN":
            aw = 3 * h * 3 * la
        else:
            aw = 1 * h * 2 * la

        # 风荷载轴向力 Nlw = 1.5 × wk × Aw
        nlw = 1.5 * wk * aw  # 1.5为风荷载分项系数γQ，见规范表4.3.1
        # 总轴向力 Nt = Nlw + 3.0
        nt = nlw + n0

        # -----------------------------
        # 3) 四大承载力验算
        # -----------------------------
        # 3.1 连墙件杆件强度/稳定验算：Nt / (φAc) ≤ [f]
        sigma = (nt * 1000) / (phi * area_c)  # N/mm²
        ratio_member = sigma / allowable_stress if allowable_stress else 0.0
        strength_passed = sigma <= allowable_stress

        # 3.2 螺栓抗拔深度验算：h ≥ Nt / (π × d × τb)
        required_anchor_depth_mm = (nt * 1000) / (
            np.pi * bolt_diameter_mm * tau_b
        )
        # 当前请求结构中未单独定义“实际锚固深度”，暂以 calculation_length_l0_mm 作为工程代理值
        actual_anchor_depth_mm = self.request_data.wall_tie_params.calculation_length_l0_mm
        anchor_ratio = (
            required_anchor_depth_mm / actual_anchor_depth_mm
            if actual_anchor_depth_mm
            else float("inf")
        )
        anchor_passed = actual_anchor_depth_mm >= required_anchor_depth_mm

        if not anchor_passed:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_ANCHOR_DEPTH_INSUFFICIENT",
                    check_item="连墙件螺栓锚固深度验算",
                    field_path="wall_tie_params.calculation_length_l0_mm",
                    current_value=round(actual_anchor_depth_mm, 3),
                    limit_value=round(required_anchor_depth_mm, 3),
                    severity="error",
                    message="连墙件螺栓锚固深度不足。",
                    suggestion="建议增大锚固深度、提高混凝土粘结强度或优化连墙件布置。",
                )
            )

        # 3.3 螺栓抗拉验算：Nt / (π × d² / 4) ≤ [ft]
        bolt_area = np.pi * bolt_diameter_mm**2 / 4
        sigma_t = (nt * 1000) / bolt_area  # N/mm²
        ratio_bolt_tension = (
            sigma_t / bolt_tensile_strength if bolt_tensile_strength else 0.0
        )
        bolt_tension_passed = sigma_t <= bolt_tensile_strength

        # 3.4 局部混凝土承压验算：
        # fcc = 0.95 × fc
        concrete_strength_map = {
            "C25": 11.9 / 0.95,
            "C30": 14.3,
            "C35": 16.7,
            "C40": 19.1,
        }
        fc = concrete_strength_map.get(concrete_grade, 14.3)
        fcc = 0.95 * fc  # 局部承压强度设计值，折减系数0.95
        local_bearing_plate_width = 5 * bolt_diameter_mm  # 垫板边长取5d的构造假定
        local_bearing_capacity = (
            local_bearing_plate_width**2 - np.pi * bolt_diameter_mm**2 / 4
        ) * fcc
        ratio_local_bearing = (
            (nt * 1000) / local_bearing_capacity
            if local_bearing_capacity > 0
            else float("inf")
        )
        local_bearing_passed = (nt * 1000) <= local_bearing_capacity

        # 3.5 扣件抗滑移验算：Nt ≤ slip_resistance
        ratio_slip = nt / slip_resistance if slip_resistance else float("inf")
        slip_passed = nt <= slip_resistance

        if not strength_passed:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_STRENGTH_EXCEEDED",
                    check_item="连墙件承载力验算",
                    field_path="wall_tie_params.model",
                    current_value=round(sigma, 3),
                    limit_value=allowable_stress,
                    severity="error",
                    message="连墙件强度或稳定性不足。",
                    suggestion="建议增大连墙件截面、减小单个连墙件控制面积或加密连墙件布置。",
                )
            )

        if not bolt_tension_passed:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_BOLT_TENSION_EXCEEDED",
                    check_item="连墙件螺栓抗拉验算",
                    field_path="wall_tie_params.bolt_diameter_d_mm",
                    current_value=round(sigma_t, 3),
                    limit_value=bolt_tensile_strength,
                    severity="error",
                    message="连墙件锚栓抗拉应力超出允许值。",
                    suggestion="建议增大螺栓直径、采用更高强度锚栓，或减小单个连墙件控制面积。",
                )
            )

        if not local_bearing_passed:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_CONCRETE_BEARING_EXCEEDED",
                    check_item="连墙件局部混凝土承压验算",
                    field_path="wall_tie_params.concrete_grade",
                    current_value=round(nt * 1000, 3),
                    limit_value=round(local_bearing_capacity, 3),
                    severity="error",
                    message="连墙件局部混凝土承压能力不足。",
                    suggestion="建议提高混凝土强度等级、增大垫板尺寸，或减小锚栓直径对应压力集中。",
                )
            )

        if not slip_passed:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_SLIP_EXCEEDED",
                    check_item="连墙件抗滑移验算",
                    field_path="wall_tie_params.fastener_connection_type",
                    current_value=round(nt, 3),
                    limit_value=slip_resistance,
                    severity="error",
                    message="扣件抗滑移承载力不足，建议增加扣件数量或缩小连墙件间距。",
                    suggestion="建议增加扣件数量、减小连墙件纵横间距，或降低迎风面积。",
                )
            )

        module_ratio = max(
            ratio_member,
            anchor_ratio,
            ratio_bolt_tension,
            ratio_local_bearing,
            ratio_slip,
        )
        self._update_max_utilization("连墙件承载力验算", module_ratio)

        result = {
            "la_m": la,
            "h_m": h,
            "wk_kn_m2": wk,
            "muz": muz,
            "tie_member_layout": tie_member_layout,
            "tie_member_layout_cn": {
                "ONE_STEP_TWO_SPAN": "一步两跨",
                "TWO_STEP_TWO_SPAN": "两步两跨",
                "TWO_STEP_THREE_SPAN": "两步三跨",
                "THREE_STEP_THREE_SPAN": "三步三跨",
            }.get(tie_member_layout, "一步两跨"),
            "l0_tie_mm": l0_tie_mm,
            "lambda_tie": round(lambda_tie, 1),
            "phi_tie": round(phi, 3),
            "i_tie_mm": i_tie_mm,
            "windward_area_aw_m2": aw,
            "area_c_mm2": area_c,
            "allowable_stress_n_mm2": allowable_stress,
            "phi": phi,
            "slip_resistance_kn": slip_resistance,
            "n0_kn": n0,
            "nlw_kn": nlw,
            "nt_kn": nt,
            "fc_n_mm2": fc,
            "fcc_n_mm2": fcc,
            "sigma_n_mm2": sigma,
            "required_anchor_depth_mm": required_anchor_depth_mm,
            "actual_anchor_depth_mm": actual_anchor_depth_mm,
            "bolt_tension_sigma_n_mm2": sigma_t,
            "bolt_tensile_strength_n_mm2": bolt_tensile_strength,
            "local_bearing_capacity_n": local_bearing_capacity,
            "strength_ratio": ratio_member,
            "anchor_ratio": anchor_ratio,
            "bolt_tension_ratio": ratio_bolt_tension,
            "local_bearing_ratio": ratio_local_bearing,
            "slip_ratio": ratio_slip,
            "governing_check_item": "连墙件承载力验算",
            "overall_passed": (
                strength_passed
                and anchor_passed
                and bolt_tension_passed
                and local_bearing_passed
                and slip_passed
            ),
        }
        self._wall_tie_result = result
        return result

    def _check_wall_tie(self) -> Dict[str, Any]:
        """Wall tie strength / anchorage / bolt / bearing / slip check."""
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行连墙件验算。")

        la = self.request_data.geometry_params.longitudinal_spacing_la_m
        h = self.request_data.geometry_params.step_height_h_m
        tie_member_layout = self.request_data.wall_tie_params.layout
        wall_tie_connection_type = self._normalize_wall_tie_connection_type(
            getattr(self.request_data.wall_tie_params, "wall_tie_connection_type", "")
            or self.request_data.wall_tie_params.connection_type
        )
        bolt_diameter_mm = float(
            getattr(self.request_data.wall_tie_params, "bolt_diameter_mm", 0.0)
            or self.request_data.wall_tie_params.bolt_diameter_d_mm
        )
        bolt_tensile_strength = (
            self.request_data.wall_tie_params.bolt_tensile_strength_n_mm2
        )
        tau_b = self.request_data.wall_tie_params.allowable_bond_strength_n_mm2
        concrete_grade = self.request_data.wall_tie_params.concrete_grade
        fastener_type = self._normalize_wall_tie_fastener_type(
            getattr(self.request_data.wall_tie_params, "fastener_type", "")
            or self.request_data.wall_tie_params.fastener_connection_type
        )
        anchor_depth_mm = float(self.request_data.wall_tie_params.anchor_depth_mm)
        calculation_length_l0_mm = float(
            self.request_data.wall_tie_params.calculation_length_l0_mm
        )
        wall_tie_tube_spec = str(
            getattr(self.request_data.wall_tie_params, "wall_tie_tube_spec", "")
            or self.request_data.wall_tie_params.model
        ).strip()

        w0 = self.request_data.material_load_params.basic_wind_pressure_w0_kn_m2
        muz = self.request_data.material_load_params.wind_height_factor_muz
        us = self.request_data.material_load_params.wind_shape_factor
        wk = w0 * muz * us

        if tie_member_layout == "ONE_STEP_TWO_SPAN":
            aw = 1 * h * 2 * la
        elif tie_member_layout == "TWO_STEP_TWO_SPAN":
            aw = 2 * h * 2 * la
        elif tie_member_layout == "TWO_STEP_THREE_SPAN":
            aw = 2 * h * 3 * la
        elif tie_member_layout == "THREE_STEP_THREE_SPAN":
            aw = 3 * h * 3 * la
        else:
            aw = 1 * h * 2 * la

        n0 = 3.0  # 双排架约束平面外变形轴向力 N0 固定取 3.0kN，JGJ/T 231-2021 第5.4.3条
        n_lw = 1.5 * wk * aw  # 风荷载产生的连墙件轴向力设计值，JGJ/T 231-2021 第5.4.4条
        n_l = n_lw + n0

        tension_stress_n_mm2: Optional[float] = None
        tension_allowable_n_mm2: Optional[float] = None
        tension_check: Optional[bool] = None
        stability_lambda: Optional[float] = None
        stability_phi: Optional[float] = None
        stability_capacity_kn: Optional[float] = None
        stability_check: Optional[bool] = None
        slip_rc_kn: Optional[float] = None
        slip_check: Optional[bool] = None
        bearing_capacity_kn: Optional[float] = None
        bearing_check: Optional[bool] = None
        anchor_capacity_kn: Optional[float] = None
        anchor_check: Optional[bool] = None

        sigma = 0.0
        allowable_stress = 0.0
        area_c: Optional[float] = None
        steel_grade = "Q235"
        i_tie_mm: Optional[float] = None
        phi: Optional[float] = None
        fc: Optional[float] = None
        fcc: Optional[float] = None
        required_anchor_depth_mm: Optional[float] = None
        actual_anchor_depth_mm: Optional[float] = None
        bolt_tension_sigma_n_mm2: Optional[float] = None
        local_bearing_capacity_n: Optional[float] = None
        slip_resistance_kn: Optional[float] = None
        bolt_area_mm2: Optional[float] = None
        bolt_f_n_mm2: Optional[float] = None
        phi_A_f_n: Optional[float] = None
        phi_A_f_kn: Optional[float] = None
        tube_area_mm2: Optional[float] = None
        tube_f_n_mm2: Optional[float] = None
        tube_phi_A_f_n: Optional[float] = None
        tube_phi_A_f_kn: Optional[float] = None
        stability_area_mm2: Optional[float] = None
        stability_f_n_mm2: Optional[float] = None
        stability_phi_A_f_n: Optional[float] = None
        stability_phi_A_f_kn: Optional[float] = None

        utilization_ratios: List[float] = []

        if wall_tie_connection_type == "anchor_bolt":
            d_inner = bolt_diameter_mm * 0.85  # 螺纹小径按 0.85d 估算，本次业务规则约定
            area_n = math.pi / 4 * d_inner**2
            tension_stress_n_mm2 = n_l * 1000 / area_n
            tension_allowable_n_mm2 = float(bolt_tensile_strength)
            tension_check = tension_stress_n_mm2 <= tension_allowable_n_mm2
            utilization_ratios.append(
                tension_stress_n_mm2 / tension_allowable_n_mm2
                if tension_allowable_n_mm2
                else float("inf")
            )

            area_c = math.pi / 4 * bolt_diameter_mm**2
            bolt_area_mm2 = area_c
            bolt_f_n_mm2 = tension_allowable_n_mm2
            tube_props = self._get_wall_tie_tube_properties(wall_tie_tube_spec)
            steel_grade = str(tube_props["steel_grade"])
            tube_area_mm2 = float(tube_props["area_mm2"])
            tube_f_n_mm2 = float(
                tube_props["allowable_stress_n_mm2"]
            )  # 连墙件钢管抗压强度设计值，JGJ/T 231-2021 表B.0.1
            i_tie_mm = float(tube_props["radius_of_gyration_mm"])
            stability_lambda = calculation_length_l0_mm / i_tie_mm
            stability_phi = self._get_phi(stability_lambda, steel_grade)
            tube_phi_A_f_n = (
                stability_phi * tube_area_mm2 * tube_f_n_mm2
            )  # 预埋螺栓式连墙件钢管稳定承载力展开值 φAf，单位 N，JGJ/T 231-2021 第5.4.3-3条
            tube_phi_A_f_kn = tube_phi_A_f_n / 1000
            stability_area_mm2 = tube_area_mm2
            stability_f_n_mm2 = tube_f_n_mm2
            stability_phi_A_f_n = tube_phi_A_f_n
            stability_phi_A_f_kn = tube_phi_A_f_kn
            stability_capacity_kn = tube_phi_A_f_kn
            stability_check = n_l <= stability_capacity_kn
            utilization_ratios.append(
                n_l / stability_capacity_kn if stability_capacity_kn else float("inf")
            )

            plate_area_mm2 = 100.0 * 100.0  # 垫片尺寸按 □100×100mm 固定取值，本次业务规则约定
            hole_area_mm2 = math.pi / 4 * bolt_diameter_mm**2
            area_l = plate_area_mm2 - hole_area_mm2
            area_ln = area_l
            beta_l = 2.0  # 局部受压强度提高系数 βl 上限值，GB 50010-2010 第6.6.1条与图6.6.2
            beta_c = 1.0  # C50 及以下混凝土强度影响系数 βc 取 1.0，GB 50010-2010 第6.3.1条
            fc = self._get_concrete_fc(concrete_grade)
            bearing_capacity_kn = (
                1.35 * beta_c * beta_l * fc * area_ln / 1000
            )  # 局部受压承载力设计值，GB 50010-2010 第6.6.1条
            bearing_check = n_l <= bearing_capacity_kn
            utilization_ratios.append(
                n_l / bearing_capacity_kn if bearing_capacity_kn else float("inf")
            )

            sigma = max(
                tension_stress_n_mm2,
                n_l * 1000 / (stability_phi * tube_area_mm2)
                if stability_phi and tube_area_mm2
                else 0.0,
            )
            allowable_stress = (
                tension_allowable_n_mm2
                if tension_stress_n_mm2 >= (
                    n_l * 1000 / (stability_phi * tube_area_mm2)
                    if stability_phi and tube_area_mm2
                    else 0.0
                )
                else tube_f_n_mm2
            )
            actual_anchor_depth_mm = anchor_depth_mm
            bolt_tension_sigma_n_mm2 = tension_stress_n_mm2
            local_bearing_capacity_n = bearing_capacity_kn * 1000 if bearing_capacity_kn else None
            fcc = 1.35 * beta_c * beta_l * fc

        elif wall_tie_connection_type in {"embedded_tube", "clamp_column"}:
            tube_props = self._get_wall_tie_tube_properties(wall_tie_tube_spec)
            steel_grade = str(tube_props["steel_grade"])
            area_c = float(tube_props["area_mm2"])
            allowable_stress = float(tube_props["allowable_stress_n_mm2"])
            tube_area_mm2 = area_c
            tube_f_n_mm2 = allowable_stress
            i_tie_mm = float(tube_props["radius_of_gyration_mm"])
            tension_stress_n_mm2 = n_l * 1000 / area_c
            tension_allowable_n_mm2 = allowable_stress
            tension_check = tension_stress_n_mm2 <= tension_allowable_n_mm2
            utilization_ratios.append(
                tension_stress_n_mm2 / tension_allowable_n_mm2
                if tension_allowable_n_mm2
                else float("inf")
            )

            stability_lambda = calculation_length_l0_mm / i_tie_mm
            stability_phi = self._get_phi(stability_lambda, steel_grade)
            tube_phi_A_f_n = (
                stability_phi * tube_area_mm2 * tube_f_n_mm2
            )  # 连墙件钢管稳定承载力展开值 φAf，单位 N，JGJ/T 231-2021 第5.4.3-3条
            tube_phi_A_f_kn = tube_phi_A_f_n / 1000
            stability_area_mm2 = tube_area_mm2
            stability_f_n_mm2 = tube_f_n_mm2
            stability_phi_A_f_n = tube_phi_A_f_n
            stability_phi_A_f_kn = tube_phi_A_f_kn
            stability_capacity_kn = (
                tube_phi_A_f_kn
            )
            stability_check = n_l <= stability_capacity_kn
            utilization_ratios.append(
                n_l / stability_capacity_kn if stability_capacity_kn else float("inf")
            )

            slip_rc_kn = (
                8.0 if fastener_type == "单扣件" else 16.0
            )  # 单扣件/双扣件抗滑承载力设计值 Rc，JGJ/T 231-2021 第5.4.3-4条
            slip_check = n_l <= slip_rc_kn
            utilization_ratios.append(n_l / slip_rc_kn if slip_rc_kn else float("inf"))

            if wall_tie_connection_type == "embedded_tube":
                perimeter_mm = (
                    math.pi * float(tube_props["outer_diameter_mm"])
                )
                anchor_capacity_kn = perimeter_mm * anchor_depth_mm * tau_b / 1000
                anchor_check = n_l <= anchor_capacity_kn
                utilization_ratios.append(
                    n_l / anchor_capacity_kn if anchor_capacity_kn else float("inf")
                )
                required_anchor_depth_mm = (
                    n_l * 1000 / (perimeter_mm * tau_b) if tau_b else None
                )
                actual_anchor_depth_mm = anchor_depth_mm

            sigma = max(
                tension_stress_n_mm2,
                n_l * 1000 / (stability_phi * area_c) if stability_phi and area_c else 0.0,
            )
            slip_resistance_kn = slip_rc_kn
            phi = stability_phi

        else:
            raise ValueError(f"不支持的连墙件连接方式: {wall_tie_connection_type}")

        phi = stability_phi

        if tension_check is False:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_TENSION_EXCEEDED",
                    check_item="连墙件受拉承载力验算",
                    field_path=(
                        "wall_tie_params.bolt_diameter_mm"
                        if wall_tie_connection_type == "anchor_bolt"
                        else "wall_tie_params.wall_tie_tube_spec"
                    ),
                    current_value=round(tension_stress_n_mm2 or 0.0, 3),
                    limit_value=round(tension_allowable_n_mm2 or 0.0, 3),
                    severity="error",
                    message="连墙件受拉承载力不足。",
                    suggestion="建议增大连墙件截面、提高材料强度，或减小单个连墙件控制面积。",
                )
            )

        if stability_check is False:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_STABILITY_EXCEEDED",
                    check_item="连墙件稳定性验算",
                    field_path="wall_tie_params.calculation_length_l0_mm",
                    current_value=round(n_l, 3),
                    limit_value=round(stability_capacity_kn or 0.0, 3),
                    severity="error",
                    message="连墙件稳定承载力不足。",
                    suggestion="建议减小计算长度、增大连墙件截面，或优化连墙件布置。",
                )
            )

        if bearing_check is False:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_CONCRETE_BEARING_EXCEEDED",
                    check_item="连墙件局部混凝土承压验算",
                    field_path="wall_tie_params.concrete_grade",
                    current_value=round(n_l, 3),
                    limit_value=round(bearing_capacity_kn or 0.0, 3),
                    severity="error",
                    message="连墙件垫片局部承压能力不足。",
                    suggestion="建议提高混凝土强度等级、增大垫片尺寸，或减小连墙件轴向力。",
                )
            )

        if anchor_check is False:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_ANCHOR_EXCEEDED",
                    check_item="连墙件握裹锚固验算",
                    field_path="wall_tie_params.anchor_depth_mm",
                    current_value=round(n_l, 3),
                    limit_value=round(anchor_capacity_kn or 0.0, 3),
                    severity="error",
                    message="连墙件预埋段握裹锚固能力不足。",
                    suggestion="建议增大预埋深度、提高粘结强度，或减小连墙件轴向力。",
                )
            )

        if slip_check is False:
            self.issues.append(
                IssueItem(
                    item_code="WALL_TIE_SLIP_EXCEEDED",
                    check_item="连墙件抗滑移验算",
                    field_path="wall_tie_params.fastener_type",
                    current_value=round(n_l, 3),
                    limit_value=round(slip_rc_kn or 0.0, 3),
                    severity="error",
                    message="扣件抗滑移承载力不足。",
                    suggestion="建议增加扣件数量、减小连墙件纵横间距，或降低迎风面积。",
                )
            )

        participated_checks = [
            tension_check,
            stability_check,
            slip_check,
            bearing_check,
            anchor_check,
        ]
        is_ok = all(check is not False for check in participated_checks)
        module_ratio = max(utilization_ratios) if utilization_ratios else 0.0
        self._update_max_utilization("连墙件承载力验算", module_ratio)

        result = {
            "connection_type": wall_tie_connection_type,
            "N_lw_kn": n_lw,
            "N0_kn": n0,
            "N_l_kn": n_l,
            "tension_stress_n_mm2": tension_stress_n_mm2,
            "tension_allowable_n_mm2": tension_allowable_n_mm2,
            "tension_check": tension_check,
            "tension_result_rt": _make_result_rt(bool(tension_check)),
            "stability_lambda": stability_lambda,
            "stability_phi": stability_phi,
            "stability_capacity_kn": stability_capacity_kn,
            "stability_check": stability_check,
            "stability_result_rt": _make_result_rt(bool(stability_check)),
            "stability_l0_mm": calculation_length_l0_mm,
            "stability_i_mm": round(i_tie_mm, 3) if i_tie_mm is not None else None,
            "stability_lambda_formula": (
                f"{calculation_length_l0_mm:g}/{round(i_tie_mm, 3):g}"
                if i_tie_mm is not None
                else None
            ),
            "stability_area_mm2": (
                round(stability_area_mm2, 2)
                if stability_area_mm2 is not None
                else None
            ),
            "stability_f_n_mm2": stability_f_n_mm2,
            "stability_phi_A_f_n": (
                round(stability_phi_A_f_n, 1)
                if stability_phi_A_f_n is not None
                else None
            ),
            "stability_phi_A_f_kn": (
                round(stability_phi_A_f_kn, 3)
                if stability_phi_A_f_kn is not None
                else None
            ),
            "wall_tie_tube_spec_display": tube_props["tube_spec"] if tube_area_mm2 is not None else None,
            "slip_Rc_kn": slip_rc_kn,
            "slip_check": slip_check,
            "slip_result_rt": (
                _make_result_rt(bool(slip_check)) if slip_check is not None else None
            ),
            "bearing_capacity_kn": bearing_capacity_kn,
            "bearing_check": bearing_check,
            "bearing_result_rt": (
                _make_result_rt(bool(bearing_check))
                if bearing_check is not None
                else None
            ),
            "anchor_capacity_kn": anchor_capacity_kn,
            "anchor_check": anchor_check,
            "anchor_result_rt": (
                _make_result_rt(bool(anchor_check))
                if anchor_check is not None
                else None
            ),
            "is_ok": is_ok,
            "la_m": la,
            "h_m": h,
            "wk_kn_m2": wk,
            "muz": muz,
            "tie_member_layout": tie_member_layout,
            "l0_tie_mm": calculation_length_l0_mm,
            "lambda_tie": round(stability_lambda, 1) if stability_lambda is not None else None,
            "phi_tie": round(stability_phi, 3) if stability_phi is not None else None,
            "i_tie_mm": i_tie_mm,
            "windward_area_aw_m2": aw,
            "area_c_mm2": area_c,
            "allowable_stress_n_mm2": allowable_stress,
            "allowable_stress_mpa": allowable_stress,
            "wall_tie_model": (
                wall_tie_tube_spec
                if wall_tie_connection_type != "anchor_bolt"
                else f"预埋螺栓 d{bolt_diameter_mm:g}"
            ),
            "wall_tie_steel_grade": steel_grade,
            "phi": phi,
            "slip_resistance_kn": slip_resistance_kn,
            "n0_kn": n0,
            "nlw_kn": n_lw,
            "nt_kn": n_l,
            "fc_n_mm2": fc,
            "fcc_n_mm2": fcc,
            "sigma_n_mm2": sigma,
            "required_anchor_depth_mm": required_anchor_depth_mm,
            "actual_anchor_depth_mm": actual_anchor_depth_mm,
            "bolt_tension_sigma_n_mm2": bolt_tension_sigma_n_mm2,
            "bolt_tensile_strength_n_mm2": bolt_tensile_strength,
            "local_bearing_capacity_n": local_bearing_capacity_n,
            "bolt_area_mm2": round(bolt_area_mm2, 2) if bolt_area_mm2 is not None else None,
            "bolt_f_n_mm2": bolt_f_n_mm2,
            "phi_A_f_n": round(phi_A_f_n, 1) if phi_A_f_n is not None else None,
            "phi_A_f_kn": round(phi_A_f_kn, 3) if phi_A_f_kn is not None else None,
            "tube_area_mm2": round(tube_area_mm2, 2) if tube_area_mm2 is not None else None,
            "tube_f_n_mm2": tube_f_n_mm2,
            "tube_phi_A_f_n": (
                round(tube_phi_A_f_n, 1) if tube_phi_A_f_n is not None else None
            ),
            "tube_phi_A_f_kn": (
                round(tube_phi_A_f_kn, 3) if tube_phi_A_f_kn is not None else None
            ),
            "strength_ratio": (
                tension_stress_n_mm2 / tension_allowable_n_mm2
                if tension_stress_n_mm2 is not None and tension_allowable_n_mm2
                else None
            ),
            "anchor_ratio": (
                n_l / anchor_capacity_kn if anchor_capacity_kn else None
            ),
            "bolt_tension_ratio": (
                tension_stress_n_mm2 / tension_allowable_n_mm2
                if tension_stress_n_mm2 is not None and tension_allowable_n_mm2
                else None
            ),
            "local_bearing_ratio": (
                n_l / bearing_capacity_kn if bearing_capacity_kn else None
            ),
            "slip_ratio": n_l / slip_rc_kn if slip_rc_kn else None,
            "governing_check_item": "连墙件承载力验算",
            "overall_passed": is_ok,
        }
        self._wall_tie_result = result
        return result

    def _check_foundation(self) -> Dict[str, Any]:
        """
        底座与地基基础验算。

        底座与地基基础验算（商用级重构版）。

        计算逻辑：
        1. 可调底座验算：Rmax = γ0 × Nmax ≤ adjustable_base_capacity_kn
        2. 地基承压验算：p = Nmax / base_plate_area_m2 ≤ fg_kpa
        """
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行底座与地基基础验算。")

        # -----------------------------
        # 1) 提取参数
        # -----------------------------
        foundation_params = self.request_data.foundation_params
        soil_type_map = {
            "COMPACTED_FILL": "压实填土",
            "CLAY": "黏土",
            "SILT": "粉土",
            "SAND": "砂土",
            "WEATHERED_ROCK": "强风化岩",
            "OTHER": "其他",
        }
        gamma_0 = self.request_data.basic_info.importance_factor
        axial_force_design_kn = self._vertical_standard_result.get("axial_force_design_kn", 0.0)
        fg_kpa = foundation_params.bearing_capacity_fg_kpa

        if foundation_params.foundation_hardened == "yes":
            area_m2 = 0.25  # 硬化地面垫板底面积取 0.25㎡，本次业务规则约定
            foundation_hardened_cn = "是"
            base_plate_area_desc = "0.25（压力扩散后等效面积）"
        else:
            area_m2 = 0.15 * 0.15  # 未硬化地面垫板按 0.15m×0.15m 取值，本次业务规则约定
            foundation_hardened_cn = "否"
            base_plate_area_desc = "0.0225"

        if foundation_params.adjustable_base_type == "B":
            adjustable_base_limit_kn = 100.0  # B 型可调底座承载力设计值，JGJ/T 231-2021 表5.1.9
            adjustable_base_type_cn = "B型 100kN"
        else:
            adjustable_base_limit_kn = 140.0  # Z 型可调底座承载力设计值，JGJ/T 231-2021 表5.1.9
            adjustable_base_type_cn = "Z型 140kN"

        foundation_params.base_plate_area_m2 = area_m2
        foundation_params.adjustable_base_capacity_kn = adjustable_base_limit_kn

        # -----------------------------
        # 2) 可调底座承载力验算
        # -----------------------------
        n_max_kn = axial_force_design_kn
        reaction_base_kn = gamma_0 * n_max_kn
        ratio_base = (
            reaction_base_kn / adjustable_base_limit_kn
            if adjustable_base_limit_kn
            else float("inf")
        )
        base_passed = reaction_base_kn <= adjustable_base_limit_kn

        if not base_passed:
            self.issues.append(
                IssueItem(
                    item_code="ADJUSTABLE_BASE_CAPACITY_EXCEEDED",
                    check_item="可调底座承载力验算",
                    field_path="foundation_params.adjustable_base_type",
                    current_value=round(reaction_base_kn, 3),
                    limit_value=adjustable_base_limit_kn,
                    severity="error",
                    message=(
                        f"可调底座受力超出允许值 {adjustable_base_limit_kn:.1f}kN。"
                    ),
                    suggestion="建议降低立杆轴力、优化架体布置，或更换更高承载力底座。",
                )
            )

        # -----------------------------
        # 3) 立杆支承面（地基）承载力验算
        # -----------------------------
        pressure_kpa = axial_force_design_kn / area_m2 if area_m2 > 0 else float("inf")
        pressure_limit_kpa = fg_kpa
        ratio_foundation = (
            pressure_kpa / pressure_limit_kpa
            if pressure_limit_kpa > 0
            else float("inf")
        )
        foundation_passed = pressure_kpa <= pressure_limit_kpa

        if not foundation_passed:
            self.issues.append(
                IssueItem(
                    item_code="FOUNDATION_BEARING_CAPACITY_EXCEEDED",
                    check_item="地基承载力验算",
                    field_path="foundation_params.foundation_hardened",
                    current_value=round(pressure_kpa, 3),
                    limit_value=round(pressure_limit_kpa, 3),
                    severity="error",
                    message="地基承载力不足，建议增大垫板面积或进行地基加固处理。",
                    suggestion="建议增大垫板面积、提高地基承载力特征值，或进行地基加固处理。",
                )
            )

        # -----------------------------
        # 4) 利用率更新与结果汇总
        # -----------------------------
        module_ratio = max(ratio_base, ratio_foundation)
        self._update_max_utilization("底座与地基承载力验算", module_ratio)

        result = {
            "axial_force_design_kn": axial_force_design_kn,
            "N_max_kn": round(n_max_kn, 3),
            "reaction_base_kn": reaction_base_kn,
            "foundation_hardened": foundation_params.foundation_hardened,
            "foundation_hardened_cn": foundation_hardened_cn,
            "adjustable_base_type": foundation_params.adjustable_base_type,
            "adjustable_base_type_cn": adjustable_base_type_cn,
            "adjustable_base_limit_kn": adjustable_base_limit_kn,
            "adjustable_base_capacity_kn": adjustable_base_limit_kn,
            "fg_kpa": fg_kpa,
            "bearing_capacity_fg_kpa": fg_kpa,
            "soil_type": soil_type_map.get(
                foundation_params.soil_type, foundation_params.soil_type
            ),
            "area_m2": area_m2,
            "base_plate_area_m2": area_m2,
            "base_plate_area_desc": base_plate_area_desc,
            "pressure_kpa": pressure_kpa,
            "base_pressure_kpa": pressure_kpa,
            "pressure_limit_kpa": pressure_limit_kpa,
            "ratio_base": ratio_base,
            "ratio_foundation": ratio_foundation,
            "base_capacity_check": base_passed,
            "bearing_check": foundation_passed,
            "base_capacity_result_rt": _make_result_rt(base_passed),
            "bearing_result_rt": _make_result_rt(foundation_passed),
            "is_ok": base_passed and foundation_passed,
            "overall_passed": base_passed and foundation_passed,
        }
        self._foundation_result = result
        return result

    def calculate(
        self,
        request_data: CalculationCheckRequest,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[List[IssueItem], ResultSummary]:
        """
        执行脚手架计算流程。

        当前 MVP 已接入：
        1. 横向横杆验算
        2. 立杆稳定性验算
        3. 连墙件承载力验算
        4. 底座与地基基础验算
        """
        self.request_data = request_data
        self.issues = []
        self.max_utilization_ratio = 0.0
        self.governing_check_item = None

        # 第一步：横向横杆验算
        horizontal_ledger_result = self._check_horizontal_ledger()

        # 第二步：立杆稳定性验算
        vertical_standard_result = self._check_vertical_standard()

        # 第三步：连墙件承载力验算
        wall_tie_result = self._check_wall_tie()

        # 第四步：底座与地基基础验算
        foundation_result = self._check_foundation()

        overall_passed = (
            horizontal_ledger_result["overall_passed"]
            and vertical_standard_result["overall_passed"]
            and wall_tie_result["overall_passed"]
            and foundation_result["overall_passed"]
        )

        # 摘要中的最大应力优先取所有应力类控制值中的最大值
        stress_candidates = [
            (
                horizontal_ledger_result["sigma_n_mm2"],
                horizontal_ledger_result["allowable_stress_n_mm2"],
            ),
            (
                vertical_standard_result["sigma_n_mm2"],
                vertical_standard_result["allowable_stress_n_mm2"],
            ),
            (
                wall_tie_result["sigma_n_mm2"],
                wall_tie_result["allowable_stress_n_mm2"],
            ),
        ]
        max_stress, _ = max(stress_candidates, key=lambda item: item[0])

        self.result_summary = ResultSummary(
            overall_passed=overall_passed,
            governing_check_item=self.governing_check_item,
            max_stress_mpa=round(max_stress, 3),
            allowable_stress_mpa=round(
                horizontal_ledger_result["allowable_stress_mpa"], 3
            ),
            max_utilization_ratio=round(self.max_utilization_ratio, 4),
            max_axial_force_kn=round(
                max(
                    vertical_standard_result["axial_force_design_kn"],
                    wall_tie_result["nt_kn"],
                    foundation_result["reaction_base_kn"],
                ),
                4,
            ),
            max_bending_moment_kn_m=round(
                max(
                    horizontal_ledger_result["max_bending_moment_kn_m"],
                    vertical_standard_result["wind_bending_moment_kn_m"],
                ),
                4,
            ),
            max_deflection_mm=round(horizontal_ledger_result["max_deflection_mm"], 4),
            deflection_limit_mm=round(horizontal_ledger_result["deflection_limit_mm"], 4),
        )

        report_path = None
        if db is not None and user_id is not None:
            try:
                self.draw_diagrams()
                report_path = self.generate_report()

                calculation_record = CalculationRecord(
                    user_id=user_id,
                    project_name=request_data.basic_info.project_name,
                    scaffold_type=request_data.scaffold_type,
                    status="passed" if self.result_summary.overall_passed else "failed",
                    overall_passed=self.result_summary.overall_passed,
                    request_snapshot=request_data.model_dump_json(),
                    result_snapshot=self.result_summary.model_dump_json(),
                    report_path=report_path,
                )
                db.add(calculation_record)
                db.commit()
            except Exception as exc:
                db.rollback()
                print(f"Failed to save calculation record: {exc}")

        return self.issues, self.result_summary

    def draw_diagrams(self) -> DiagramUrls:
        """
        根据横向横杆验算结果绘制受力简图、剪力图、弯矩图和挠度图。

        当前基于“简支梁 + 均布荷载 + 跨中集中力”模型生成示意图，
        图片保存到本地 static/diagrams/{calculation_id}/ 目录下，
        并返回对应的相对访问路径。
        """
        # -----------------------------
        # 1) 安全提取数据
        # -----------------------------
        ledger_result = self._horizontal_ledger_result or {}
        calculation_id = self.calculation_id or "test_calc"

        L = float(ledger_result.get("lb_m") or 1.0)  # 跨度，m
        q = float(ledger_result.get("self_weight_design_kn_m") or 0.0)  # 均布荷载，kN/m
        P = float(ledger_result.get("concentrated_load_design_k") or 0.0)  # 跨中集中力，kN
        v_max = float(ledger_result.get("max_deflection_mm") or 0.0)  # 最大挠度，mm

        if L <= 0:
            L = 1.0

        # -----------------------------
        # 2) 构建坐标与内力数组
        # -----------------------------
        x = np.linspace(0, L, 200)

        # 简支梁在均布荷载 q 与跨中集中力 P 作用下的支座反力
        reaction_a = q * L / 2 + P / 2

        # 剪力图：跨中点前后考虑集中力突变
        V = np.where(
            x < L / 2,
            reaction_a - q * x,
            reaction_a - q * x - P,
        )

        # 弯矩图：跨中点后附加集中力产生的弯矩项
        M = np.where(
            x < L / 2,
            reaction_a * x - 0.5 * q * (x**2),
            reaction_a * x - 0.5 * q * (x**2) - P * (x - L / 2),
        )

        # 挠度图：MVP 阶段采用半波正弦曲线做视觉示意
        v = -v_max * np.sin(np.pi * x / L)

        # -----------------------------
        # 3) 图片目录准备
        # -----------------------------
        dir_path = os.path.join("static", "diagrams", calculation_id)
        os.makedirs(dir_path, exist_ok=True)

        force_file = os.path.join(dir_path, "force.png")
        shear_file = os.path.join(dir_path, "shear.png")
        moment_file = os.path.join(dir_path, "moment.png")
        deflection_file = os.path.join(dir_path, "deflection.png")
        beam_y = 0.0

        # -----------------------------
        # 4) 绘制受力简图
        # -----------------------------
        fig, ax = plt.subplots(figsize=(12, 4))

        # 梁本体
        ax.plot([0, L], [beam_y, beam_y], color="black", linewidth=2)

        # 两端支座：使用三角形标记示意
        ax.scatter([0, L], [-0.03, -0.03], marker="^", s=220, color="black", zorder=3)

        # 均布荷载：顶部虚线 + 多个向下箭头
        q_line_y = 0.35
        ax.plot([0, L], [q_line_y, q_line_y], linestyle="--", color="royalblue", linewidth=1.5)
        for xi in np.linspace(0, L, 9):
            ax.annotate(
                "",
                xy=(xi, beam_y),
                xytext=(xi, q_line_y),
                arrowprops=dict(arrowstyle="->", color="royalblue", lw=1.2),
            )
        ax.text(L * 0.02, q_line_y + 0.06, f"均布荷载 q = {q:.3f} kN/m", color="royalblue")

        # 跨中集中力
        ax.annotate(
            "",
            xy=(L / 2, beam_y),
            xytext=(L / 2, 0.55),
            arrowprops=dict(arrowstyle="->", color="crimson", lw=2),
        )
        ax.text(L / 2 + 0.03, 0.42, f"P = {P:.3f} kN", color="crimson")

        # 跨度与支座标注
        ax.text(0, -0.15, "A 支座", ha="center")
        ax.text(L, -0.15, "B 支座", ha="center")
        ax.text(L / 2, -0.24, f"L = {L:.3f} m", ha="center")

        ax.set_title("横向横杆受力简图")
        ax.set_xlim(-0.05 * L, 1.05 * L)
        ax.set_ylim(-0.3, 0.75)
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(force_file, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # -----------------------------
        # 5) 绘制剪力图
        # -----------------------------
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(x, V, color="seagreen", linewidth=2, label="V(x)")
        ax.fill_between(x, V, 0, color="mediumseagreen", alpha=0.25)
        ax.axhline(0, color="black", linewidth=1)

        max_shear_idx = int(np.argmax(np.abs(V)))
        max_shear_val = float(V[max_shear_idx])
        max_shear_x = float(x[max_shear_idx])
        ax.scatter([max_shear_x], [max_shear_val], color="red", zorder=3)
        ax.annotate(
            f"最大剪力 = {abs(max_shear_val):.3f} kN",
            xy=(max_shear_x, max_shear_val),
            xytext=(max_shear_x, max_shear_val + (0.4 if max_shear_val >= 0 else -0.4)),
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red",
        )

        ax.set_title("横向横杆剪力图")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("V (kN)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend()
        fig.tight_layout()
        fig.savefig(shear_file, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # -----------------------------
        # 6) 绘制弯矩图
        # 建筑结构习惯：正弯矩绘制在下方，故取 -M
        # -----------------------------
        M_plot = -M
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(x, M_plot, color="darkorange", linewidth=2, label="-M(x)")
        ax.fill_between(x, M_plot, 0, color="orange", alpha=0.25)
        ax.axhline(0, color="black", linewidth=1)

        max_moment_idx = int(np.argmax(M))
        max_moment_val = float(M[max_moment_idx])
        max_moment_x = float(x[max_moment_idx])
        ax.scatter([max_moment_x], [-max_moment_val], color="red", zorder=3)
        ax.annotate(
            f"最大弯矩 = {max_moment_val:.3f} kN·m",
            xy=(max_moment_x, -max_moment_val),
            xytext=(max_moment_x, -max_moment_val - 0.25),
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red",
        )

        ax.set_title("横向横杆弯矩图")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("-M (kN·m)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend()
        fig.tight_layout()
        fig.savefig(moment_file, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # -----------------------------
        # 7) 绘制挠度图
        # -----------------------------
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(x, v, color="purple", linewidth=2, label="v(x)")
        ax.fill_between(x, v, 0, color="mediumpurple", alpha=0.25)
        ax.axhline(0, color="black", linewidth=1)

        max_deflection_idx = int(np.argmin(v))
        max_deflection_val = abs(float(v[max_deflection_idx]))
        max_deflection_x = float(x[max_deflection_idx])
        ax.scatter([max_deflection_x], [float(v[max_deflection_idx])], color="red", zorder=3)
        ax.annotate(
            f"最大挠度 = {max_deflection_val:.3f} mm",
            xy=(max_deflection_x, float(v[max_deflection_idx])),
            xytext=(0, 30),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red",
        )

        ax.set_title("横向横杆挠度图")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("v (mm)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend()
        fig.tight_layout()
        fig.savefig(deflection_file, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # -----------------------------
        # 8) 返回相对访问路径
        # -----------------------------
        self.diagram_urls = DiagramUrls(
            force_diagram_url=f"/static/diagrams/{calculation_id}/force.png",
            shear_diagram_url=f"/static/diagrams/{calculation_id}/shear.png",
            moment_diagram_url=f"/static/diagrams/{calculation_id}/moment.png",
            deflection_diagram_url=f"/static/diagrams/{calculation_id}/deflection.png",
        )
        return self.diagram_urls

    def generate_report(self) -> Optional[str]:
        """
        使用 docxtpl 渲染 Word 计算书。

        无论本轮计算是否通过，均生成 Word 计算书；
        若模板缺失或关键资源不存在，则打印提示并返回 None。
        """
        if not self.result_summary or not self.request_data:
            self.report_download_url = None
            return None

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        template_path = os.path.join(
            project_root, "templates", "exterior_scaffold_template.docx"
        )
        if not os.path.exists(template_path):
            print(f"Word 模板不存在：{template_path}")
            self.report_download_url = None
            return None

        reports_dir = os.path.join(project_root, "static", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        output_path = os.path.join(reports_dir, f"{self.calculation_id}.docx")

        doc = DocxTemplate(template_path)

        material_params = self.request_data.material_load_params
        pole_type = str(material_params.vertical_tube_spec).strip()
        if pole_type == "standard_b":
            material_params.pole_tube_spec = "Φ48.3×3.2"
        elif pole_type == "heavy_z":
            material_params.pole_tube_spec = "Φ60.3×3.2"

        material_params.ledger_tube_spec = "Φ48.3×2.5"
        material_params.brace_tube_spec = "Φ38×2.5"

        wall_tie_params = self.request_data.wall_tie_params
        wall_tie_connection_type = self._normalize_wall_tie_connection_type(
            getattr(wall_tie_params, "wall_tie_connection_type", "")
            or wall_tie_params.connection_type
        )
        fastener_type = self._normalize_wall_tie_fastener_type(
            getattr(wall_tie_params, "fastener_type", "")
            or wall_tie_params.fastener_connection_type
        )
        tie_member_layout = str(wall_tie_params.layout).strip()
        tie_layout_map = {
            "ONE_STEP_TWO_SPAN": {"step_count": 1, "span_count": 2, "label": "一步两跨"},
            "TWO_STEP_TWO_SPAN": {"step_count": 2, "span_count": 2, "label": "两步两跨"},
            "TWO_STEP_THREE_SPAN": {"step_count": 2, "span_count": 3, "label": "两步三跨"},
            "THREE_STEP_THREE_SPAN": {
                "step_count": 3,
                "span_count": 3,
                "label": "三步三跨",
            },
        }
        tie_layout_config = tie_layout_map.get(
            tie_member_layout,
            tie_layout_map["ONE_STEP_TWO_SPAN"],
        )
        wall_tie_context = dict(self._wall_tie_result)
        connection_type_map = {
            "anchor_bolt": "预埋螺栓式",
            "embedded_tube": "预埋短钢管式",
            "clamp_column": "钢管抱柱式",
        }
        wall_tie_context.update(
            {
                "connection_type": wall_tie_connection_type,
                "connection_type_cn": connection_type_map.get(
                    wall_tie_connection_type, "预埋螺栓式"
                ),
                "tie_member_layout_cn": tie_layout_config["label"],
                "calculation_length_l0_mm": wall_tie_params.calculation_length_l0_mm,
                "N_lw_kn": wall_tie_context.get("N_lw_kn", wall_tie_context.get("nlw_kn")),
                "N_l_kn": wall_tie_context.get("N_l_kn", wall_tie_context.get("nt_kn")),
                "L_l": (
                    self.request_data.geometry_params.longitudinal_spacing_la_m
                    * tie_layout_config["span_count"]
                ),
                "H_l": (
                    self.request_data.geometry_params.step_height_h_m
                    * tie_layout_config["step_count"]
                ),
                "fastener_type": fastener_type,
                "anchor_depth_mm": wall_tie_params.anchor_depth_mm,
                "allowable_bond_strength_n_mm2": (
                    wall_tie_params.allowable_bond_strength_n_mm2
                ),
            }
        )

        if wall_tie_connection_type == "anchor_bolt":
            bolt_diameter_mm = float(
                getattr(wall_tie_params, "bolt_diameter_mm", 0.0)
                or wall_tie_params.bolt_diameter_d_mm
            )
            d_inner_mm = (
                bolt_diameter_mm * 0.85
            )  # 螺纹小径按 0.85d 估算，本次业务规则约定
            plate_area_mm2 = 100.0 * 100.0  # 垫片尺寸按 □100×100mm 固定取值，本次业务规则约定
            hole_area_mm2 = math.pi / 4 * bolt_diameter_mm**2
            wall_tie_context.update(
                {
                    "bolt_diameter_mm": bolt_diameter_mm,
                    "A_n_mm2": math.pi / 4 * d_inner_mm**2,
                    "A_l_mm2": plate_area_mm2 - hole_area_mm2,
                    "beta_l": 2.0,  # 局部受压强度提高系数 βl 上限值，GB 50010-2010 第6.6.1条与图6.6.2
                    "fc_n_mm2": wall_tie_context.get("fc_n_mm2")
                    or self._get_concrete_fc(wall_tie_params.concrete_grade),
                }
            )
        else:
            wall_tie_tube_spec = str(
                getattr(wall_tie_params, "wall_tie_tube_spec", "") or wall_tie_params.model
            ).strip()
            normalized_tube_spec = (
                wall_tie_tube_spec.replace("x", "×").replace("X", "×")
            )
            normalized_tube_spec = {
                "Φ48×3.2": "Φ48×3.25",
                "Φ48.3×3.2": "Φ48×3.25",
                "Φ48.3×3.25": "Φ48×3.25",
                "Φ48.3×2.75": "Φ48×2.75",
            }.get(normalized_tube_spec, normalized_tube_spec)
            tube_props = self._get_wall_tie_tube_properties(normalized_tube_spec)
            wall_tie_context.update(
                {
                    "tube_spec": normalized_tube_spec,
                    "outer_diameter_mm": tube_props["outer_diameter_mm"],
                    "A_n_mm2": tube_props["area_mm2"],
                }
            )

        foundation_context = dict(getattr(self, "_foundation_result", {}))

        context = {
            "req": self.request_data.model_dump(),
            "summary": self.result_summary.model_dump(),
            "hl": self._horizontal_ledger_result,
            "vs": self._vertical_standard_result,
            "wt": wall_tie_context,
            "fd": foundation_context,
        }
        context["req"]["material_load_params"]["vertical_tube_spec"] = (
            _VERTICAL_TUBE_DISPLAY_NAMES.get(
                self.request_data.material_load_params.vertical_tube_spec,
                self.request_data.material_load_params.vertical_tube_spec,
            )
        )
        context["summary"]["overall_passed_text"] = (
            "各项验算均满足要求，方案安全可行。"
            if self.result_summary.overall_passed
            else "部分验算项未通过，方案需调整。"
        )
        # 枚举值中文翻译
        context["cn"] = {
            "safety_level": {
                "LEVEL_I": "Ⅰ级",
                "LEVEL_II": "Ⅱ级",
            }.get(
                self.request_data.basic_info.safety_level,
                self.request_data.basic_info.safety_level,
            ),
            "plank_type": {
                "STEEL_PLANK": "冲压钢脚手板",
                "WOOD_PLANK": "木脚手板",
                "BAMBOO_PLANK": "竹脚手板",
            }.get(
                self.request_data.material_load_params.plank_type,
                self.request_data.material_load_params.plank_type,
            ),
            "connection_type": {
                "EXPANSION_BOLT": "膨胀螺栓",
                "CHEMICAL_BOLT": "化学螺栓",
                "EMBEDDED": "预埋件",
            }.get(
                self.request_data.wall_tie_params.connection_type,
                self.request_data.wall_tie_params.connection_type,
            ),
            "fastener_connection_type": {
                "DOUBLE": "双扣件",
                "SINGLE": "单扣件",
            }.get(
                self.request_data.wall_tie_params.fastener_connection_type,
                self.request_data.wall_tie_params.fastener_connection_type,
            ),
            "section_type": {
                "TUBE": "钢管",
                "ANGLE": "角钢",
                "CHANNEL": "槽钢",
            }.get(
                self.request_data.wall_tie_params.section_type,
                self.request_data.wall_tie_params.section_type,
            ),
        }
        context = _format_context_value(context)

        # 动态配图插入：根据已生成的相对 URL 推导本地物理路径
        if self.diagram_urls:
            image_mappings = {
                "img_force": self.diagram_urls.force_diagram_url,
                "img_shear": self.diagram_urls.shear_diagram_url,
                "img_moment": self.diagram_urls.moment_diagram_url,
                "img_deflection": self.diagram_urls.deflection_diagram_url,
            }
            for context_key, relative_url in image_mappings.items():
                if not relative_url:
                    continue
                image_path = os.path.join(
                    project_root, relative_url.lstrip("/").replace("/", os.sep)
                )
                if not os.path.exists(image_path):
                    print(f"配图文件不存在：{image_path}")
                    continue
                context[context_key] = InlineImage(doc, image_path, width=Mm(140))

        doc.render(context)
        doc.save(output_path)

        self.report_download_url = f"/static/reports/{self.calculation_id}.docx"
        return self.report_download_url
