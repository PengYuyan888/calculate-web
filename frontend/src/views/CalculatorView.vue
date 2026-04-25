<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { calculate, getReportUrl } from '../api/scaffold.js'
import NavBar from '../components/NavBar.vue'
import LeftPanel from '../components/LeftPanel.vue'
import DiagramView from '../components/DiagramView.vue'
import ResultPanel from '../components/ResultPanel.vue'

const loading = ref(false)
const result = ref(null)
const reportUrl = ref('')
const requestError = ref('')
const autoStarted = ref(false)

const form = reactive({
  basic_info: {
    project_name: 'XX商业综合体项目',
    construction_part: '1#楼外立面',
    prepared_by: '张工',
    safety_level: 'LEVEL_II',
    importance_factor: 1.0,
    scaffold_clearance_m: 0.0,
    calculation_date: new Date().toISOString().slice(0, 10)
  },
  geometry_params: {
    longitudinal_spacing_la_m: 1.5,
    transverse_spacing_lb_m: 0.9,
    step_height_h_m: 2.0,
    erection_height_hs_m: 22.7,
    row_count: 2,
    tie_member_layout: 'ONE_STEP_TWO_SPAN',
    sweeping_rod_height_m: 0.2,
    guardrail_height_m: 1.2,
    guardrail_top_height_h1_m: 1.5,
    sweeping_rod_height_h2_mm: 500,
    inner_pole_to_wall_m: 0.3,
    diagonal_brace_layout: '每隔3跨一设'
  },
  material_load_params: {
    vertical_tube_spec: 'standard_b',
    horizontal_tube_spec: 'Q355_PHI48X3_25',
    pole_model: 'B-LG-300',
    pole_tube_spec: 'Φ48.3×3.2',
    ledger_model: 'B-SG',
    ledger_tube_spec: 'Φ48.3×2.5',
    brace_model: 'B-XG',
    brace_tube_spec: 'Φ48.3×2.5',
    brace_material_form: '专用斜杆',
    plank_type: 'STEEL_PLANK',
    plank_laying_method: '1步1设',
    single_plank_width_b_mm: 250,
    hook_count_per_side_j: 2,
    hook_spacing_s_mm: 200,
    plank_self_weight_kn_m2: 0.35,
    safety_net_self_weight_kn_m2: 0.01,
    toe_board_type: '木脚手板挡板',
    toe_board_laying_method: '1步1设',
    toe_board_self_weight_kn_m: 0.17,
    working_layer_count: 2,
    construction_live_load_kn_m2: 3.0,
    basic_wind_pressure_w0_kn_m2: 0.3,
    terrain_roughness_category: 'C',
    wind_shape_factor: 1.3,
    wind_height_factor_muz: 1.052
  },
  wall_tie_params: {
    layout: 'ONE_STEP_TWO_SPAN',
    connection_type: 'EXPANSION_BOLT',
    calculation_length_l0_mm: 1500,
    anchor_depth_mm: 150,
    section_type: 'TUBE',
    model: 'Φ48×3.2',
    fastener_connection_type: 'DOUBLE',
    bolt_diameter_d_mm: 18,
    bolt_tensile_strength_n_mm2: 170,
    concrete_grade: 'C30',
    allowable_bond_strength_n_mm2: 1.5
  },
  foundation_params: {
    soil_type: 'COMPACTED_FILL',
    bearing_capacity_fg_kpa: 120,
    sole_plate_area_m2: 0.25,
    adjustable_base_capacity_kn: 100
  },
  location_info: {
    province: '',
    city: ''
  }
})

watch(
  () => form.geometry_params.tie_member_layout,
  (val) => {
    form.wall_tie_params.layout = val
  },
  { immediate: true }
)

async function handleSubmit() {
  loading.value = true
  result.value = null
  reportUrl.value = ''
  requestError.value = ''

  try {
    form.wall_tie_params.layout = form.geometry_params.tie_member_layout

    const payload = {
      scaffold_type: 'RINGLOCK_DOUBLE_ROW_EXTERIOR',
      basic_info: { ...form.basic_info },
      geometry_params: { ...form.geometry_params },
      material_load_params: { ...form.material_load_params },
      wall_tie_params: { ...form.wall_tie_params },
      foundation_params: { ...form.foundation_params },
      location_info:
        form.location_info.province && form.location_info.city
          ? { ...form.location_info }
          : null
    }

    const res = await calculate(payload)
    result.value = res.data

    if (res.data.report_download_url) {
      reportUrl.value = getReportUrl(res.data.report_download_url)
    }
  } catch (error) {
    console.error('计算失败', error)
    const detail = error?.response?.data?.detail
    const message = error?.response?.data?.message

    if (Array.isArray(detail)) {
      requestError.value = detail
        .map((item) => item?.msg || JSON.stringify(item))
        .filter(Boolean)
        .join('；')
    } else if (typeof detail === 'string' && detail.trim()) {
      requestError.value = detail.trim()
    } else if (typeof message === 'string' && message.trim()) {
      requestError.value = message.trim()
    } else {
      requestError.value = '请求失败，请确认后端服务已在 localhost:8000 运行。'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  const stepParam = Number(params.get('step') || '')

  if (!Number.isNaN(stepParam) && stepParam > 0) {
    form.geometry_params.step_height_h_m = stepParam
  }

  if (params.get('autostart') === '1' && !autoStarted.value) {
    autoStarted.value = true
    window.setTimeout(() => {
      handleSubmit()
    }, 300)
  }
})
</script>

<template>
  <div class="calculator-page">
    <NavBar />
    <main class="calculator-body">
      <LeftPanel
        class="calculator-left-panel"
        :form="form"
        :loading="loading"
        @submit="handleSubmit"
      />

      <section class="right-panel">
        <div class="diagram-area">
          <div class="diagram-top-row">
            <article class="diagram-card plan-card">
              <div class="diagram-header">
                <div class="diagram-title-group">
                  <span class="diagram-dot diagram-dot--blue"></span>
                  <div>
                    <h3>平面图</h3>
                  </div>
                </div>
              </div>
              <div class="diagram-body">
                <DiagramView
                  type="plan"
                  :la="form.geometry_params.longitudinal_spacing_la_m"
                  :lb="form.geometry_params.transverse_spacing_lb_m"
                  :h="form.geometry_params.step_height_h_m"
                  :hs="form.geometry_params.erection_height_hs_m"
                  :wall-gap="form.geometry_params.inner_pole_to_wall_m"
                  :diagonal-brace="form.geometry_params.diagonal_brace_layout"
                  :tie-member-layout="form.geometry_params.tie_member_layout"
                />
              </div>
            </article>

            <article class="diagram-card section-card">
              <div class="diagram-header">
                <div class="diagram-title-group">
                  <span class="diagram-dot diagram-dot--green"></span>
                  <div>
                    <h3>剖面图</h3>
                  </div>
                </div>
              </div>
              <div class="diagram-body">
                <DiagramView
                  type="section"
                  :la="form.geometry_params.longitudinal_spacing_la_m"
                  :lb="form.geometry_params.transverse_spacing_lb_m"
                  :h="form.geometry_params.step_height_h_m"
                  :hs="form.geometry_params.erection_height_hs_m"
                  :wall-gap="form.geometry_params.inner_pole_to_wall_m"
                  :diagonal-brace="form.geometry_params.diagonal_brace_layout"
                  :tie-member-layout="form.geometry_params.tie_member_layout"
                />
              </div>
            </article>
          </div>

          <div class="diagram-bottom-row">
            <article class="diagram-card elev-card">
              <div class="diagram-header">
                <div class="diagram-title-group">
                  <span class="diagram-dot diagram-dot--brown"></span>
                  <div>
                    <h3>立面图</h3>
                  </div>
                </div>
              </div>
              <div class="diagram-body">
                <DiagramView
                  type="elevation"
                  :la="form.geometry_params.longitudinal_spacing_la_m"
                  :lb="form.geometry_params.transverse_spacing_lb_m"
                  :h="form.geometry_params.step_height_h_m"
                  :hs="form.geometry_params.erection_height_hs_m"
                  :wall-gap="form.geometry_params.inner_pole_to_wall_m"
                  :diagonal-brace="form.geometry_params.diagonal_brace_layout"
                  :tie-member-layout="form.geometry_params.tie_member_layout"
                />
              </div>
            </article>
          </div>
        </div>

        <section class="result-area">
          <ResultPanel
            :loading="loading"
            :result="result"
            :report-url="reportUrl"
            :request-error="requestError"
          />
        </section>
      </section>
    </main>
  </div>
</template>

<style scoped>
.calculator-page {
  height: 100%;
  width: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
  overflow: visible;
}

.calculator-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.calculator-left-panel {
  width: 25%;
  flex: 0 0 25%;
  min-width: 280px;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.right-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.diagram-area {
  flex: 4;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 10px 12px 10px;
  box-sizing: border-box;
  overflow: hidden;
  min-height: 0;
}

.diagram-top-row {
  height: calc(50% - 4px);
  min-height: 0;
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  overflow: hidden;
}

.diagram-bottom-row {
  height: calc(50% - 4px);
  min-height: 0;
  flex-shrink: 0;
  margin-bottom: 2px;
  overflow: hidden;
}

.result-area {
  flex-shrink: 0;
  overflow: visible;
  min-height: 0;
  padding: 4px 10px 12px 10px;
  box-sizing: border-box;
}

.diagram-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  padding: 10px 10px 1px;
  overflow: visible;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  background: #ffffff;
  box-sizing: border-box;
}

.plan-card,
.section-card {
  flex: 1;
}

.elev-card {
  width: 100%;
}

.diagram-header {
  flex-shrink: 0;
}

.diagram-title-group {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.diagram-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 3px;
  flex-shrink: 0;
}

.diagram-dot--blue {
  background: #185fa5;
}

.diagram-dot--green {
  background: #0f6e56;
}

.diagram-dot--brown {
  background: #854f0b;
}

.diagram-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: #2f3440;
  line-height: 1.2;
  margin-bottom: 0;
}

.diagram-body {
  flex: 1;
  min-height: 0;
  width: 100%;
  height: 100%;
  display: block;
  overflow: hidden;
  border: 1px dashed #e8e8e8;
  border-radius: 6px;
  background: #fafafa;
  margin-top: 6px;
}
</style>
