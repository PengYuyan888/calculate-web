from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


NumericOrText = Union[int, float, str]


class BasicInfo(BaseModel):
    """基本信息参数组。"""

    project_name: str = Field(
        default="XX商业综合体项目",
        description="工程名称，用于计算书首页标题及项目归档标识。",
    )
    construction_part: str = Field(
        default="1#楼外立面",
        description="施工部位，用于标识脚手架搭设的具体楼栋或区域。",
    )
    prepared_by: str = Field(
        default="张工",
        description="编制人姓名，用于计算书责任人落款。",
    )
    calculation_date: date = Field(
        default=date(2026, 3, 25),
        description="计算日期，格式为 YYYY-MM-DD，用于报告生成时间记录。",
    )
    safety_level: Literal["LEVEL_I", "LEVEL_II"] = Field(
        default="LEVEL_II",
        description="脚手架安全等级；LEVEL_I 表示 I 级，LEVEL_II 表示 II 级。",
    )
    importance_factor: Literal[1.0, 1.1] = Field(
        default=1.0,
        description="结构重要性系数 γ0，通常取 1.0 或 1.1。",
    )
    # 前端已移除“架体离地高度”输入项；保留该字段仅为兼容历史请求数据，不参与当前后端验算。
    scaffold_clearance_m: float = Field(
        default=0.0,
        ge=0,
        description="架体离地高度，单位 m；用于描述架体底部与地面的净空或起步搭设高度。",
    )


class GeometryParams(BaseModel):
    """架体几何参数组。"""

    longitudinal_spacing_la_m: float = Field(
        default=1.5,
        gt=0,
        description="立杆纵距 la，单位 m，表示沿脚手架纵向相邻立杆中心距。",
    )
    transverse_spacing_lb_m: float = Field(
        default=0.9,
        gt=0,
        description="立杆横距 lb，单位 m，表示脚手架内外排立杆之间的水平距离。",
    )
    step_height_h_m: float = Field(
        default=1.8,
        gt=0,
        description="立杆步距 h，单位 m，表示相邻水平杆步层高度。",
    )
    erection_height_hs_m: float = Field(
        default=24.0,
        gt=0,
        description="搭设总高度 Hs，单位 m，用于立杆稳定性及风荷载计算。",
    )
    row_count: Literal[2] = Field(
        default=2,
        description="架体排数，MVP 阶段固定为双排脚手架。",
    )
    tie_member_layout: Literal[
        "ONE_STEP_TWO_SPAN",
        "TWO_STEP_THREE_SPAN",
        "TWO_STEP_TWO_SPAN",
        "THREE_STEP_THREE_SPAN",
    ] = Field(
        default="ONE_STEP_TWO_SPAN",
        description="连墙件布置方式编码，用于验算计算长度、控制面积与风荷载分配。",
    )
    sweeping_rod_height_m: float = Field(
        default=0.2,
        ge=0,
        description="扫地杆距地高度，单位 m，保留原字段以兼容已有计算逻辑。",
    )
    guardrail_height_m: float = Field(
        default=1.2,
        gt=0,
        description="防护栏杆高度，单位 m，保留原字段以兼容已有前后端逻辑。",
    )
    guardrail_top_height_h1_m: float = Field(
        default=1.5,
        gt=0,
        description="顶部防护栏杆高 h1，单位 m，用于真实搭设参数与构配件统计。",
    )
    sweeping_rod_height_h2_mm: int = Field(
        default=500,
        ge=0,
        description="纵横向扫地杆距立杆底距离 h2，单位 mm，常用于构造验算与细部描述。",
    )
    inner_pole_to_wall_m: float = Field(
        default=0.3,
        ge=0,
        description="内排架距墙距离或依次横距，单位 m，用于架体贴墙布置与荷载控制面积计算。",
    )
    diagonal_brace_layout: str = Field(
        default="每隔3跨一设",
        description="外斜杆布置方式，例如“每隔3跨一设”“满设”等，用于构造说明和后续拓展验算。",
    )


class MaterialLoadParams(BaseModel):
    """材料与荷载参数组。"""

    vertical_tube_spec: Literal["standard_b", "heavy_z"] = Field(
        default="standard_b",
        description="盘扣立杆类型：standard_b=标准型B型，heavy_z=重型Z型",
    )
    horizontal_tube_spec: Literal[
        "Q355_PHI48X3_25",
        "Q355_PHI48X3_0",
        "Q355_PHI48X2_75",
        "Q235_PHI48X3_25",
        "Q235_PHI48X2_75",
    ] = Field(
        default="Q355_PHI48X3_25",
        description="水平杆钢管规格编码，后端根据编码关联物理属性，保留以兼容现有逻辑。",
    )
    pole_model: str = Field(
        default="B-LG-300",
        description="立杆型号，用于映射盘扣构配件产品型号与材料参数。",
    )
    pole_tube_spec: str = Field(
        default="Φ48.3x3.2",
        description="立杆钢管类型或截面规格，用于实际产品选型与截面属性查取。",
    )
    ledger_model: str = Field(
        default="B-SG",
        description="纵横向水平杆型号，用于构配件选型、重量统计和构造描述。",
    )
    ledger_tube_spec: str = Field(
        default="Φ48.3x2.5",
        description="纵横向水平杆钢管类型，用于横杆强度、刚度及自重计算。",
    )
    brace_model: str = Field(
        default="B-XG",
        description="外斜杆型号，用于斜杆构件说明与后续稳定验算扩展。",
    )
    brace_tube_spec: str = Field(
        default="Φ48.3x2.5",
        description="外斜杆钢管截面类型，用于材料统计及后续斜杆受力验算。",
    )
    brace_material_form: str = Field(
        default="专用斜杆",
        description="外斜杆材料形式，用于构造说明，如'专用斜杆'。",
    )
    plank_type: Literal["STEEL_PLANK", "WOOD_PLANK", "BAMBOO_PLANK"] = Field(
        default="STEEL_PLANK",
        description="脚手板类型编码，用于荷载、材性及模板渲染。",
    )
    plank_laying_method: str = Field(
        default="1步1设",
        description="脚手板铺设方式，例如“1步1设”“隔步铺设”等，用于荷载统计。",
    )
    single_plank_width_b_mm: int = Field(
        default=250,
        gt=0,
        description="单块脚手板宽度 b，单位 mm，用于板荷载向横杆传递的控制宽度计算。",
    )
    hook_count_per_side_j: int = Field(
        default=2,
        ge=1,
        description="单块脚手板一侧爪钩数量 j，用于集中反力计算。",
    )
    hook_spacing_s_mm: int = Field(
        default=200,
        gt=0,
        description="爪钩间距 s，单位 mm，用于真实构造描述及后续更精细受力分析。",
    )
    plank_self_weight_kn_m2: float = Field(
        default=0.35,
        ge=0,
        description="脚手板自重标准值，单位 kN/㎡，用于恒载统计。",
    )
    safety_net_self_weight_kn_m2: float = Field(
        default=0.01,
        ge=0,
        description="密目安全网自重标准值，单位 kN/㎡，用于围护材料恒载统计。",
    )
    toe_board_type: str = Field(
        default="木脚手板挡板",
        description="挡脚板类型，用于围护构造说明及荷载选型。",
    )
    toe_board_laying_method: str = Field(
        default="1步1设",
        description="挡脚板铺设方式，用于挡脚板自重折算与构造说明。",
    )
    toe_board_self_weight_kn_m: float = Field(
        default=0.14,
        ge=0,
        description="挡脚板线荷载标准值，单位 kN/m，用于围护材料荷载统计。",
    )
    working_layer_count: int = Field(
        default=2,
        ge=1,
        description="同时作业层数，用于施工活荷载最不利组合计算。",
    )
    construction_live_load_kn_m2: Literal[1.0, 2.0, 3.0] = Field(
        default=3.0,
        description="施工均布活荷载标准值，单位 kN/㎡；1.0=防护脚手架，2.0=装修脚手架，3.0=砌筑作业脚手架，依据规范表4.2.5。",
    )
    basic_wind_pressure_w0_kn_m2: Optional[float] = Field(
        default=None,
        ge=0,
        description="基本风压 w0，单位 kN/㎡；可手动输入，也可由项目所在地自动反查后回填。",
    )
    terrain_roughness_category: Literal["A", "B", "C", "D"] = Field(
        default="C",
        description="地面粗糙度类别，用于风荷载高度变化系数取值。",
    )
    wind_shape_factor: Literal[1.0, 1.3] = Field(
        default=1.3,
        description="风荷载体型系数；1.0=建筑墙体已砌筑，1.3=建筑墙体未砌筑。",
    )
    wind_height_factor_muz: Optional[float] = Field(
        default=None,
        gt=0,
        description="风荷载高度变化系数 μz；可手动输入，也可由项目所在地海拔与搭设高度自动推导。",
    )


class WallTieParams(BaseModel):
    """连墙件参数分组。"""

    layout: str = Field(
        default="ONE_STEP_TWO_SPAN",
        description="连墙件布置方式，推荐与 geometry_params.tie_member_layout 保持一致。",
    )
    wall_tie_connection_type: Literal[
        "anchor_bolt", "embedded_tube", "clamp_column"
    ] = Field(
        default="anchor_bolt",
        description="连墙件连接方式：anchor_bolt=预埋螺栓式，embedded_tube=预埋短钢管式，clamp_column=钢管抱柱式",
    )
    connection_type: str = Field(
        default="EXPANSION_BOLT",
        description="连墙件与主体结构连接方式的兼容字段；允许旧值 EXPANSION_BOLT/CHEMICAL_BOLT/EMBEDDED 或新值 anchor_bolt/embedded_tube/clamp_column。",
    )
    calculation_length_l0_mm: float = Field(
        default=1500.0,
        gt=0,
        description="连墙件计算长度 l0，单位 mm，用于稳定性与长细比验算。",
    )
    anchor_depth_mm: float = Field(
        default=150.0,
        gt=0,
        description="锚固/预埋深度，单位mm",
    )
    bolt_diameter_mm: Optional[float] = Field(
        default=20.0,
        gt=0,
        description="螺栓直径，单位mm，仅预埋螺栓式使用",
    )
    section_type: str = Field(
        default="TUBE",
        description="连墙件截面类型；TUBE 代表钢管截面。",
    )
    model: str = Field(
        default="Φ48x3.2",
        description="连墙件型号或截面规格，用于材料查表与截面验算。",
    )
    wall_tie_tube_spec: Optional[str] = Field(
        default="Φ48×3.25",
        description="连墙件钢管规格，仅短钢管式和抱柱式使用",
    )
    fastener_type: Optional[str] = Field(
        default="双扣件",
        description="扣件类型：单扣件/双扣件",
    )
    fastener_connection_type: str = Field(
        default="DOUBLE",
        description="连墙件与脚手架扣件连接方式；DOUBLE 代表双扣件连接。",
    )
    bolt_diameter_d_mm: int = Field(
        default=18,
        gt=0,
        description="锚栓或螺栓直径 d，单位 mm，用于锚固与抗拉验算。",
    )
    bolt_tensile_strength_n_mm2: float = Field(
        default=170.0,
        gt=0,
        description="螺栓抗拉强度设计值，单位 N/mm²。",
    )
    concrete_grade: str = Field(
        default="C30",
        description="混凝土强度等级，如C20/C25/C30/C35/C40",
    )
    allowable_bond_strength_n_mm2: float = Field(
        default=1.5,
        gt=0,
        description="混凝土与螺栓表面的容许粘结强度，单位 N/mm²。",
    )


class FoundationParams(BaseModel):
    """地基基础参数组。"""

    foundation_hardened: Literal["yes", "no"] = Field(
        default="yes",
        description="外架基础是否硬化：yes=是，no=否",
    )
    adjustable_base_type: Literal["B", "Z"] = Field(
        default="B",
        description="可调底座类型：B=B型100kN，Z=Z型140kN",
    )
    soil_type: Literal[
        "COMPACTED_FILL",
        "CLAY",
        "SILT",
        "SAND",
        "WEATHERED_ROCK",
        "OTHER",
    ] = Field(
        default="COMPACTED_FILL",
        description="地基土类型，用于承载力取值及地基处理建议。",
    )
    bearing_capacity_fg_kpa: float = Field(
        default=120.0,
        gt=0,
        description="地基承载力特征值 fg，单位 kPa。",
    )
    base_plate_area_m2: Optional[float] = Field(
        default=None,
        description="垫板底面积，单位㎡；由后端根据 foundation_hardened 自动计算。",
    )
    adjustable_base_capacity_kn: Optional[float] = Field(
        default=None,
        description="可调底座承载力设计值，单位kN；由后端根据 adjustable_base_type 自动赋值。",
    )


class LocationInfo(BaseModel):
    """项目所在地信息。"""

    province: str = Field(description="省份名称，如“北京市”。")
    city: str = Field(description="城市名称，如“北京”。")
    code: Optional[str] = Field(
        default=None,
        description="6 位官方行政区划代码，优先用于精确匹配风参数参考数据。",
    )


class CalculationCheckRequest(BaseModel):
    """盘扣式双排外脚手架验算请求体。"""

    scaffold_type: Literal["RINGLOCK_DOUBLE_ROW_EXTERIOR"] = Field(
        default="RINGLOCK_DOUBLE_ROW_EXTERIOR",
        description="脚手架类型，MVP 阶段固定为盘扣式双排外脚手架。",
    )
    basic_info: BasicInfo = Field(
        default_factory=BasicInfo,
        description="基本信息分组。",
    )
    geometry_params: GeometryParams = Field(
        default_factory=GeometryParams,
        description="架体几何参数分组。",
    )
    material_load_params: MaterialLoadParams = Field(
        default_factory=MaterialLoadParams,
        description="材料与荷载参数分组。",
    )
    wall_tie_params: WallTieParams = Field(
        default_factory=WallTieParams,
        description="连墙件参数分组。",
    )
    foundation_params: FoundationParams = Field(
        default_factory=FoundationParams,
        description="地基基础参数分组。",
    )
    location_info: Optional[LocationInfo] = Field(
        default=None,
        description="项目所在地信息；传入后端后可自动补算基本风压与风压高度变化系数。",
    )


class WindParamsResolveRequest(BaseModel):
    """风参数解析请求体。"""

    province: str = Field(description="省份名称，如“北京市”。")
    city: str = Field(description="城市名称，如“北京”。")
    code: Optional[str] = Field(
        default=None,
        description="6 位官方行政区划代码；优先用于定位目标城市，若该城市缺少风参数则继续按模糊或就近规则解析。",
    )
    roughness: Literal["A", "B", "C", "D"] = Field(
        description="地面粗糙度类别。",
    )
    erection_height_hs_m: float = Field(
        gt=0,
        description="脚手架搭设高度 Hs，单位 m。",
    )


class WindParamsResolveResponse(BaseModel):
    """风参数解析响应体。"""

    w0_kn_m2: float = Field(description="重现期 10 年基本风压，单位 kN/㎡。")
    altitude_m: float = Field(description="城市参考海拔，单位 m。")
    effective_height_m: float = Field(
        description="离海平面有效高度，单位 m。",
    )
    wind_height_factor_muz: float = Field(
        description="按附录 A 表 A.0.1 计算得到的风压高度变化系数 μz。",
    )
    matched_city: str = Field(
        description="实际命中风参数参考数据的城市名称。",
    )
    match_type: Literal[
        "exact",
        "fuzzy",
        "nearby_same_province",
        "nearby_national",
    ] = Field(
        description="匹配方式：exact / fuzzy / nearby_same_province / nearby_national。",
    )
    distance_km: Optional[float] = Field(
        default=None,
        description="就近匹配时的球面距离，单位 km；精确或模糊匹配时为 null。",
    )
    is_fallback: bool = Field(
        description="若 match_type 不为 exact，则为 true。",
    )


class ResultSummary(BaseModel):
    """计算结果摘要。"""

    overall_passed: bool = Field(description="整体验算是否通过。")
    governing_check_item: Optional[str] = Field(
        default=None,
        description="控制性验算项名称。",
    )
    max_stress_mpa: Optional[float] = Field(
        default=None,
        description="控制截面最大计算应力，单位 MPa。",
    )
    allowable_stress_mpa: Optional[float] = Field(
        default=None,
        description="允许应力或设计强度控制值，单位 MPa。",
    )
    max_utilization_ratio: Optional[float] = Field(
        default=None,
        description="最不利验算项利用率，大于 1 表示不通过。",
    )
    max_axial_force_kn: Optional[float] = Field(
        default=None,
        description="立杆最大轴力设计值 N，单位 kN。",
    )
    max_bending_moment_kn_m: Optional[float] = Field(
        default=None,
        description="最大弯矩设计值，单位 kN·m。",
    )
    max_deflection_mm: Optional[float] = Field(
        default=None,
        description="最大挠度，单位 mm。",
    )


    deflection_limit_mm: Optional[float] = Field(
        default=None,
        description="本次横杆验算使用的挠度限值，单位mm",
    )


class IssueItem(BaseModel):
    """不通过项或参数告警信息。"""

    item_code: str = Field(description="问题编码。")
    check_item: str = Field(description="问题所属验算项或校验项。")
    field_path: str = Field(description="对应前端字段路径。")
    current_value: Optional[NumericOrText] = Field(
        default=None,
        description="当前计算值或用户输入值。",
    )
    limit_value: Optional[NumericOrText] = Field(
        default=None,
        description="规范限值、设计值或推荐值。",
    )
    severity: Literal["warning", "error"] = Field(
        description="问题严重级别。",
    )
    message: str = Field(description="具体提示信息。")
    suggestion: str = Field(description="建议修改方案。")


class DiagramUrls(BaseModel):
    """后端生成配图的访问路径。"""

    force_diagram_url: Optional[str] = Field(
        default=None,
        description="受力简图图片访问路径。",
    )
    shear_diagram_url: Optional[str] = Field(
        default=None,
        description="剪力图图片访问路径。",
    )
    moment_diagram_url: Optional[str] = Field(
        default=None,
        description="弯矩图图片访问路径。",
    )
    deflection_diagram_url: Optional[str] = Field(
        default=None,
        description="挠度变形图图片访问路径。",
    )


class CalculationCheckResponse(BaseModel):
    """盘扣式双排外脚手架验算响应体。"""

    status: Literal["success", "failed"] = Field(
        description="业务处理状态；success 表示通过，failed 表示失败或未通过。",
    )
    message: str = Field(description="总体提示信息。")
    calculation_id: str = Field(description="本次计算任务唯一标识。")
    result_summary: ResultSummary = Field(description="计算结果摘要。")
    issues: List[IssueItem] = Field(
        default_factory=list,
        description="不通过项或参数告警列表，通过时返回空数组。",
    )
    diagram_urls: DiagramUrls = Field(description="后端生成配图的访问路径。")
    report_download_url: Optional[str] = Field(
        default=None,
        description="最终 Word 计算书下载链接，未生成时为 null。",
    )
    generated_at: datetime = Field(description="响应生成时间，ISO 8601 格式。")
