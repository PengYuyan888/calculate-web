from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage

from calculators.base import BaseCalculator
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


def _build_stability_table(raw: str) -> Dict[int, float]:
    """Parse appendix-C style rows into a per-integer lookup table."""
    table: Dict[int, float] = {}
    for line in raw.strip().splitlines():
        parts = line.split()
        base_lambda = int(parts[0])
        for offset, phi in enumerate(parts[1:]):
            table[base_lambda + offset] = float(phi)
    return table


# Appendix C stability coefficient tables used by the vertical standard check.
# The public PDF text layer contains obvious OCR artifacts for Q235 at λ=13 and λ=163;
# those two points are normalized to 0.966 and 0.145 to preserve the tabulated monotonic sequence.
_STABILITY_FACTOR_TABLES = {
    "Q235": _build_stability_table(
        """
        0 1.000 1.000 0.999 0.998 0.997 0.996 0.995 0.994 0.993 0.992
        10 0.974 0.971 0.968 0.966 0.962 0.959 0.955 0.952 0.949 0.945
        20 0.942 0.938 0.934 0.930 0.927 0.923 0.919 0.915 0.911 0.907
        30 0.903 0.899 0.895 0.891 0.886 0.882 0.878 0.873 0.869 0.864
        40 0.860 0.855 0.850 0.846 0.841 0.836 0.831 0.826 0.821 0.816
        50 0.811 0.806 0.801 0.795 0.790 0.785 0.780 0.774 0.769 0.763
        60 0.758 0.752 0.747 0.741 0.735 0.729 0.724 0.718 0.712 0.706
        70 0.700 0.694 0.688 0.682 0.676 0.670 0.664 0.658 0.651 0.645
        80 0.639 0.633 0.626 0.620 0.613 0.607 0.600 0.594 0.587 0.581
        90 0.574 0.567 0.561 0.554 0.547 0.540 0.534 0.527 0.520 0.513
        100 0.506 0.499 0.492 0.485 0.479 0.472 0.465 0.458 0.451 0.444
        110 0.437 0.430 0.423 0.416 0.409 0.402 0.396 0.389 0.382 0.375
        120 0.369 0.362 0.355 0.349 0.342 0.336 0.329 0.323 0.316 0.310
        130 0.304 0.297 0.291 0.285 0.279 0.273 0.267 0.261 0.255 0.250
        140 0.244 0.239 0.233 0.228 0.223 0.218 0.213 0.208 0.203 0.199
        150 0.194 0.190 0.185 0.181 0.177 0.173 0.169 0.165 0.162 0.158
        160 0.154 0.151 0.148 0.145 0.142 0.139 0.136 0.133 0.131 0.128
        170 0.126 0.123 0.121 0.119 0.117 0.115 0.113 0.111 0.109 0.108
        180 0.106 0.104 0.103 0.101 0.100 0.099 0.097 0.096 0.095 0.094
        190 0.093 0.091 0.090 0.089 0.089 0.088 0.087 0.086 0.085 0.084
        200 0.083 0.082 0.081 0.080 0.080 0.079 0.078 0.077 0.076 0.075
        210 0.074 0.073 0.072 0.071 0.070 0.069 0.068 0.068 0.067 0.066
        220 0.065 0.064 0.063 0.062 0.061 0.060 0.059 0.058 0.057 0.057
        230 0.056 0.055 0.054 0.053 0.052 0.051 0.050 0.049 0.049 0.048
        240 0.047 0.046 0.045 0.044 0.043 0.042 0.041 0.041 0.040 0.039
        250 0.038
        """
    ),
    "Q355": _build_stability_table(
        """
        0 1.000 1.000 1.000 0.999 0.998 0.997 0.996 0.995 0.994 0.993
        10 0.971 0.968 0.965 0.962 0.958 0.955 0.951 0.948 0.944 0.941
        20 0.937 0.933 0.930 0.926 0.922 0.918 0.914 0.910 0.906 0.902
        30 0.898 0.894 0.889 0.885 0.881 0.876 0.872 0.867 0.863 0.858
        40 0.854 0.849 0.844 0.840 0.835 0.830 0.825 0.820 0.815 0.810
        50 0.805 0.800 0.795 0.790 0.785 0.779 0.774 0.769 0.763 0.758
        60 0.752 0.747 0.741 0.736 0.730 0.724 0.719 0.713 0.707 0.701
        70 0.695 0.689 0.683 0.677 0.671 0.665 0.659 0.653 0.646 0.640
        80 0.634 0.627 0.621 0.615 0.608 0.602 0.595 0.589 0.582 0.575
        90 0.569 0.562 0.555 0.548 0.542 0.535 0.528 0.521 0.514 0.507
        100 0.500 0.493 0.487 0.480 0.473 0.466 0.459 0.452 0.445 0.438
        110 0.431 0.425 0.418 0.411 0.404 0.398 0.391 0.384 0.378 0.371
        120 0.365 0.358 0.352 0.346 0.339 0.333 0.327 0.321 0.315 0.309
        130 0.303 0.297 0.291 0.286 0.280 0.275 0.269 0.264 0.259 0.254
        140 0.249 0.244 0.239 0.234 0.230 0.225 0.221 0.216 0.212 0.208
        150 0.204 0.200 0.196 0.192 0.188 0.185 0.181 0.178 0.175 0.171
        160 0.168 0.165 0.162 0.160 0.157 0.154 0.152 0.149 0.147 0.145
        170 0.142 0.140 0.138 0.136 0.134 0.132 0.130 0.128 0.126 0.124
        180 0.122 0.120 0.119 0.117 0.115 0.114 0.112 0.111 0.109 0.108
        190 0.106 0.105 0.104 0.102 0.101 0.100 0.098 0.097 0.096 0.095
        200 0.094 0.093 0.092 0.091 0.090 0.089 0.088 0.087 0.086 0.085
        210 0.084 0.083 0.082 0.081 0.081 0.080 0.079 0.078 0.077 0.076
        220 0.075 0.074 0.073 0.073 0.072 0.071 0.070 0.069 0.068 0.067
        230 0.066 0.065 0.064 0.063 0.062 0.061 0.060 0.059 0.058 0.057
        240 0.056 0.055 0.054 0.053 0.052 0.051 0.050 0.049 0.047 0.046
        250 0.045
        """
    ),
}

_VERTICAL_TUBE_PROPERTIES = {
    "Q355_PHI48X3_25": {
        "steel_grade": "Q355",
        "area_mm2": 453.0,
        "radius_of_gyration_mm": 16.0,
        "w_section_mm3": 4797.0,
        "allowable_stress_n_mm2": 300.0,
    },
    "Q355_PHI48X3_0": {
        "steel_grade": "Q355",
        "area_mm2": 424.0,
        "radius_of_gyration_mm": 16.3,
        "w_section_mm3": 4491.0,
        "allowable_stress_n_mm2": 300.0,
    },
    "Q235_PHI48X3_25": {
        "steel_grade": "Q235",
        "area_mm2": 453.0,
        "radius_of_gyration_mm": 16.0,
        "w_section_mm3": 4797.0,
        "allowable_stress_n_mm2": 205.0,
    },
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
        if spec not in _VERTICAL_TUBE_PROPERTIES:
            raise ValueError(f"不支持的立杆钢管规格: {spec}")
        return _VERTICAL_TUBE_PROPERTIES[spec]

    def _get_stability_factor(
        self, lambda_val: float, steel_grade: str = "Q355"
    ) -> float:
        """根据 JGJ/T 231-2021 附录 C 查表并线性插值获取稳定系数 φ。"""
        if steel_grade not in _STABILITY_FACTOR_TABLES:
            raise ValueError(f"不支持的钢材牌号: {steel_grade}")

        table = _STABILITY_FACTOR_TABLES[steel_grade]
        min_lambda = min(table)
        max_lambda = max(table)
        clamped_lambda = max(float(min_lambda), min(float(lambda_val), float(max_lambda)))
        lower_lambda = int(clamped_lambda)

        if lower_lambda >= max_lambda or clamped_lambda == lower_lambda:
            return table[lower_lambda]

        upper_lambda = lower_lambda + 1
        lower_phi = table[lower_lambda]
        upper_phi = table[upper_lambda]
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
        q1_k = 0.028  # 横杆自重线荷载标准值，kN/m
        w_section = 3920.0  # 横杆截面抵抗矩 W，mm³
        allowable_stress = 205.0  # 抗弯强度设计值 [f]，N/mm²
        elastic_modulus = 206000.0  # N/mm^2
        section_inertia = w_section * 24.0  # mm^4

        # -----------------------------
        # 3) 承载能力极限状态
        # -----------------------------
        # 设计线荷载 q = b × (1.3 × Gkjb + 1.5 × Qkjj)
        line_load_design = b * (1.3 * gkjb + 1.5 * qkjj)  # kN/m
        # 支座反力 R = q × la / j（单个爪钩或单侧分配反力）
        support_reaction_component = line_load_design * la / j  # kN
        # 横杆自重设计值 q1 = 1.3 × q1_k
        self_weight_design = 1.3 * q1_k  # kN/m

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
        deflection_limit = min(lb_mm / 150, 10.0)  # mm
        deflection_ratio = (
            max_deflection / deflection_limit if deflection_limit else 0.0
        )
        deflection_passed = max_deflection <= deflection_limit

        # -----------------------------
        # 7) 盘扣节点抗剪验算
        # -----------------------------
        # 节点受剪力设计值 F_R = γ0 × R1
        node_shear_design = gamma_0 * support_reaction_design  # kN
        shear_limit = 40.0  # kN
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

        # 系统常量（真实计算书简化映射）
        gkdb = 0.17  # 挡脚板线荷载，kN/m
        gkmw = 0.01  # 安全网面荷载，kN/㎡
        m1 = 0.147  # 立杆单重
        m2 = 0.050  # 纵向横杆单重
        m3 = 0.033  # 横向横杆单重
        m4 = 0.089  # 外斜杆单重

        w0 = self.request_data.material_load_params.basic_wind_pressure_w0_kn_m2
        muz = self.request_data.material_load_params.wind_height_factor_muz
        us = self.request_data.material_load_params.wind_shape_factor

        # 计算有效步数 n = int((Hs - h1 - h2/1000) / h)
        n = max(1, int((hs - h1 - h2_mm / 1000) / h))

        # 连墙件布置方式对应的计算长度系数 μ
        mu_map = {
            "ONE_STEP_TWO_SPAN": 1.3,
            "TWO_STEP_TWO_SPAN": 1.5,
            "TWO_STEP_THREE_SPAN": 1.8,
        }
        mu = mu_map.get(tie_member_layout, 1.3)

        # -----------------------------
        # 2) 荷载累加：计算 NG1k、NG2k、NQ1k
        # -----------------------------
        # 内排立杆结构自重：
        # NG1k_inner = (m1×Hs/3) + m2×(n+1) + m3×(n+1)/2
        tube_props = self._get_vertical_tube_properties()
        steel_grade = str(tube_props["steel_grade"])
        area = float(tube_props["area_mm2"])  # A，mm²
        radius_of_gyration = float(tube_props["radius_of_gyration_mm"])  # mm
        w_section = float(tube_props["w_section_mm3"])  # W，mm³
        allowable_stress = float(tube_props["allowable_stress_n_mm2"])  # [f]，N/mm²

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
        n1 = 1.3 * (ng1k_inner + ng2k_inner) + 0.9 * 1.5 * nq1k
        n2 = 1.3 * (ng1k_outer + ng2k_outer) + 0.9 * 1.5 * nq1k
        axial_force_design_kn = max(n1, n2)

        # -----------------------------
        # 3) 长细比验算
        # -----------------------------
        effective_length_m = mu * h  # m
        lambda_val = effective_length_m * 1000 / radius_of_gyration
        lambda_limit = 210.0
        lambda_ratio = lambda_val / lambda_limit if lambda_limit else 0.0
        slenderness_passed = lambda_val <= lambda_limit

        if not slenderness_passed:
            self.issues.append(
                IssueItem(
                    item_code="VERTICAL_STANDARD_SLENDERNESS_EXCEEDED",
                    check_item="立杆长细比验算",
                    field_path="geometry_params.step_height_h_m",
                    current_value=round(lambda_val, 3),
                    limit_value=lambda_limit,
                    severity="error",
                    message=(
                        f"立杆长细比为 {lambda_val:.3f}，"
                        f"已超过限值 {lambda_limit:.3f}。"
                    ),
                    suggestion="建议减小步距 h、优化连墙件布置，或降低立杆计算长度系数。",
                )
            )

        self._update_max_utilization("立杆长细比验算", lambda_ratio)
        phi = self._get_stability_factor(lambda_val, steel_grade)

        # -----------------------------
        # 4) 风荷载弯矩计算
        # -----------------------------
        # wk = w0 × μz × us
        wk = w0 * muz * us
        # Mw = 0.9 × 1.5 × wk × la × h² / 10
        mw = 0.9 * 1.5 * wk * la * (h**2) / 10  # kN·m

        # -----------------------------
        # 5) 稳定性组合应力验算
        # -----------------------------
        # σ = N/(φA) + Mw/W
        sigma = (
            (axial_force_design_kn * 1000) / (phi * area)
            + (mw * 1_000_000) / w_section
        )  # N/mm²
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
            "n1_kn": n1,
            "n2_kn": n2,
            "axial_force_design_kn": axial_force_design_kn,
            "effective_length_m": effective_length_m,
            "lambda_val": lambda_val,
            "lambda_limit": lambda_limit,
            "steel_grade": steel_grade,
            "phi": phi,
            "wind_bending_moment_kn_m": mw,
            "sigma_n_mm2": sigma,
            "stability_ratio": stability_ratio,
            "lambda_ratio": lambda_ratio,
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
        area_c = 450.0  # Ac，mm²
        allowable_stress = 205.0  # [f]，N/mm²
        phi = 0.634  # 杆件稳定系数 φ
        n0 = 3.0  # 平面外变形附加轴向力 N0，kN

        # 扣件抗滑移承载力设计值：单扣件 8.0kN，双扣件 16.0kN
        slip_resistance = 16.0 if fastener_connection_type == "DOUBLE" else 8.0

        # -----------------------------
        # 2) 连墙件轴向力计算
        # -----------------------------
        if tie_member_layout == "ONE_STEP_TWO_SPAN":
            aw = 1 * h * 2 * la
        elif tie_member_layout == "TWO_STEP_TWO_SPAN":
            aw = 2 * h * 2 * la
        elif tie_member_layout == "TWO_STEP_THREE_SPAN":
            aw = 2 * h * 3 * la
        else:
            aw = 1 * h * 2 * la

        # 风荷载轴向力 Nlw = 1.5 × wk × Aw
        nlw = 1.5 * wk * aw
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
        fcc = 0.95 * fc
        local_bearing_plate_width = 5 * bolt_diameter_mm
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
            }.get(tie_member_layout, "一步两跨"),
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

    def _check_foundation(self) -> Dict[str, Any]:
        """
        底座与地基基础验算。

        底座与地基基础验算（商用级重构版）。

        计算逻辑：
        1. 可调底座验算：Rmax = γ0 × Nmax ≤ adjustable_base_capacity_kn
        2. 地基承压验算：p = Nmax / sole_plate_area_m2 ≤ fg_kpa
        """
        if self.request_data is None:
            raise ValueError("request_data 未初始化，无法执行底座与地基基础验算。")

        # -----------------------------
        # 1) 提取参数
        # -----------------------------
        gamma_0 = self.request_data.basic_info.importance_factor
        axial_force_design_kn = self._vertical_standard_result.get("axial_force_design_kn", 0.0)
        fg_kpa = self.request_data.foundation_params.bearing_capacity_fg_kpa
        area_m2 = self.request_data.foundation_params.sole_plate_area_m2
        adjustable_base_limit_kn = (
            self.request_data.foundation_params.adjustable_base_capacity_kn
        )

        # -----------------------------
        # 2) 可调底座承载力验算
        # -----------------------------
        reaction_base_kn = gamma_0 * axial_force_design_kn
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
                    field_path="foundation_params.adjustable_base_capacity_kn",
                    current_value=round(reaction_base_kn, 3),
                    limit_value=adjustable_base_limit_kn,
                    severity="error",
                    message="可调底座受力超出允许值 100kN。",
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
                    field_path="foundation_params.sole_plate_area_m2",
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
            "reaction_base_kn": reaction_base_kn,
            "adjustable_base_limit_kn": adjustable_base_limit_kn,
            "fg_kpa": fg_kpa,
            "area_m2": area_m2,
            "pressure_kpa": pressure_kpa,
            "pressure_limit_kpa": pressure_limit_kpa,
            "ratio_base": ratio_base,
            "ratio_foundation": ratio_foundation,
            "overall_passed": base_passed and foundation_passed,
        }
        self._foundation_result = result
        return result

    def calculate(
        self, request_data: CalculationCheckRequest
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
        max_stress, allowable_stress = max(stress_candidates, key=lambda item: item[0])

        self.result_summary = ResultSummary(
            overall_passed=overall_passed,
            governing_check_item=self.governing_check_item,
            max_stress_mpa=round(max_stress, 3),
            allowable_stress_mpa=round(allowable_stress, 3),
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
        )
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

        context = {
            "req": self.request_data.model_dump(),
            "summary": self.result_summary.model_dump(),
            "hl": self._horizontal_ledger_result,
            "vs": self._vertical_standard_result,
            "wt": self._wall_tie_result,
            "fd": getattr(self, "_foundation_result", {}),
        }
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
