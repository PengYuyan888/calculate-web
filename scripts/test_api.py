import json

import requests


API_URL = "http://127.0.0.1:8000/api/v1/calculations/exterior-scaffold/check"

PAYLOAD = {
    "scaffold_type": "RINGLOCK_DOUBLE_ROW_EXTERIOR",
    "basic_info": {
        "project_name": "XX商业综合体项目",
        "construction_part": "1#楼外立面",
        "prepared_by": "张工",
        "calculation_date": "2026-03-25",
        "safety_level": "LEVEL_II",
        "importance_factor": 1.0,
        "scaffold_clearance_m": 0.0,
    },
    "geometry_params": {
        "longitudinal_spacing_la_m": 1.5,
        "transverse_spacing_lb_m": 0.9,
        "step_height_h_m": 1.8,
        "erection_height_hs_m": 24.0,
        "row_count": 2,
        "tie_member_layout": "ONE_STEP_TWO_SPAN",
        "sweeping_rod_height_m": 0.2,
        "guardrail_height_m": 1.2,
        "guardrail_top_height_h1_m": 1.5,
        "sweeping_rod_height_h2_mm": 500,
        "inner_pole_to_wall_m": 0.3,
        "diagonal_brace_layout": "每隔3跨一设",
    },
    "material_load_params": {
        "vertical_tube_spec": "Q355_PHI48X3_25",
        "horizontal_tube_spec": "Q355_PHI48X3_25",
        "pole_model": "B-LG-300",
        "pole_tube_spec": "Φ48.3x3.2",
        "ledger_model": "B-SG",
        "ledger_tube_spec": "Φ48.3x2.5",
        "brace_model": "B-XG",
        "brace_tube_spec": "Φ48.3x2.5",
        "plank_type": "STEEL_PLANK",
        "plank_laying_method": "1步1设",
        "single_plank_width_b_mm": 250,
        "hook_count_per_side_j": 2,
        "hook_spacing_s_mm": 200,
        "plank_self_weight_kn_m2": 0.35,
        "safety_net_self_weight_kn_m2": 0.01,
        "toe_board_type": "木脚手板挡板",
        "toe_board_laying_method": "1步1设",
        "toe_board_self_weight_kn_m": 0.14,
        "working_layer_count": 2,
        "construction_live_load_kn_m2": 3.0,
        "basic_wind_pressure_w0_kn_m2": 0.3,
        "terrain_roughness_category": "C",
        "wind_shape_factor": 1.3,
        "wind_height_factor_muz": 1.052,
    },
    "wall_tie_params": {
        "layout": "ONE_STEP_TWO_SPAN",
        "connection_type": "EXPANSION_BOLT",
        "calculation_length_l0_mm": 1500,
        "section_type": "TUBE",
        "model": "Φ48x3.2",
        "fastener_connection_type": "DOUBLE",
        "bolt_diameter_d_mm": 18,
        "bolt_tensile_strength_n_mm2": 170.0,
        "concrete_grade": "C30",
        "allowable_bond_strength_n_mm2": 1.5,
    },
    "foundation_params": {
        "soil_type": "COMPACTED_FILL",
        "bearing_capacity_fg_kpa": 120.0,
        "sole_plate_area_m2": 0.05,
        "adjustable_base_capacity_kn": 100.0,
    },
}


def main() -> None:
    response = requests.post(API_URL, json=PAYLOAD, timeout=30)
    print(f"HTTP Status Code: {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
