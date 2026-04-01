<script setup>
import { computed } from 'vue'

const props = defineProps({
  form: {
    type: Object,
    required: true
  }
})

const stepCount = computed(() => {
  const hs = Number(props.form.geometry_params.erection_height_hs_m || 0)
  const h1 = Number(props.form.geometry_params.guardrail_top_height_h1_m || 0)
  const h2 = Number(props.form.geometry_params.sweeping_rod_height_h2_mm || 0)
  const h = Number(props.form.geometry_params.step_height_h_m || 0)

  if (!h) {
    return 0
  }

  return Math.max(0, Math.floor((hs - h1 - h2 / 1000) / h))
})
</script>

<template>
  <div class="tab-pane">
    <div class="section-title">基本信息</div>
    <div class="form-section">
      <div class="field">
        <label>工程名称</label>
        <input v-model="form.basic_info.project_name" type="text">
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>施工部位</label>
          <input v-model="form.basic_info.construction_part" type="text">
        </div>
        <div class="field">
          <label>编制人</label>
          <input v-model="form.basic_info.prepared_by" type="text">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>安全等级</label>
          <div class="select-wrapper">
            <select v-model="form.basic_info.safety_level">
              <option value="LEVEL_II">Ⅱ级</option>
              <option value="LEVEL_I">Ⅰ级</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>重要性系数 γ0</label>
          <div class="select-wrapper">
            <select v-model.number="form.basic_info.importance_factor">
              <option :value="1.0">1.0</option>
              <option :value="1.1">1.1</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>架体离地高度(m)</label>
          <input v-model.number="form.basic_info.scaffold_clearance_m" type="number" step="0.1">
        </div>
        <div class="field">
          <label>计算日期</label>
          <input v-model="form.basic_info.calculation_date" type="date">
        </div>
      </div>
    </div>

    <div class="section-title">架体几何参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>立杆纵距 la(m)</label>
          <div class="select-wrapper">
            <select v-model.number="form.geometry_params.longitudinal_spacing_la_m">
              <option :value="0.9">0.9</option>
              <option :value="1.2">1.2</option>
              <option :value="1.5">1.5</option>
              <option :value="1.8">1.8</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>立杆横距 lb(m)</label>
          <div class="select-wrapper">
            <select v-model.number="form.geometry_params.transverse_spacing_lb_m">
              <option :value="0.6">0.6</option>
              <option :value="0.9">0.9</option>
              <option :value="1.2">1.2</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>立杆步距 h(m)</label>
          <div class="select-wrapper">
            <select v-model.number="form.geometry_params.step_height_h_m">
              <option :value="1.0">1.0</option>
              <option :value="1.5">1.5</option>
              <option :value="2.0">2.0</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>搭设高度 Hs(m)</label>
          <input v-model.number="form.geometry_params.erection_height_hs_m" type="number" step="0.1">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>栏杆高 h1(m)</label>
          <input v-model.number="form.geometry_params.guardrail_top_height_h1_m" type="number" step="0.1">
        </div>
        <div class="field">
          <label>扫地杆距底 h2(mm)</label>
          <input v-model.number="form.geometry_params.sweeping_rod_height_h2_mm" type="number" step="1">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>内排距墙(m)</label>
          <input v-model.number="form.geometry_params.inner_pole_to_wall_m" type="number" step="0.1">
        </div>
        <div class="field">
          <label>连墙件布置</label>
          <div class="select-wrapper">
            <select v-model="form.geometry_params.tie_member_layout">
              <option value="ONE_STEP_TWO_SPAN">一步两跨</option>
              <option value="TWO_STEP_TWO_SPAN">两步两跨</option>
              <option value="TWO_STEP_THREE_SPAN">两步三跨</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>外斜杆布置</label>
          <div class="select-wrapper">
            <select v-model="form.geometry_params.diagonal_brace_layout">
              <option value="每隔1跨一设">隔1布1</option>
              <option value="每隔2跨一设">隔2布1</option>
              <option value="每隔3跨一设">隔3布1</option>
              <option value="每隔4跨一设">隔4布1</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>步数 n</label>
          <input :value="`${stepCount} 步`" type="text" readonly class="readonly-input">
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-pane {
  display: flex;
  flex-direction: column;
}

.section-title {
  height: 26px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  background: #f0f0f0;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  color: #888888;
  font-size: 12px;
  font-weight: 500;
}

.form-section {
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-row-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.field {
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field label {
  font-size: 12px;
  color: #666666;
}

.field input,
.field select {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  height: 30px;
  border: 1px solid #cccccc;
  border-radius: 5px;
  padding: 0 8px;
  font-size: 13px;
  color: #333333;
  background: #ffffff;
  outline: none;
}

.select-wrapper {
  position: relative;
  width: 100%;
  min-width: 0;
}

.select-wrapper select {
  appearance: none;
  -webkit-appearance: none;
  padding-right: 28px;
  font-size: 14px;
}

.select-wrapper::after {
  content: '▾';
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #999999;
  font-size: 16px;
  line-height: 1;
  pointer-events: none;
}

.readonly-input,
.field input[readonly] {
  background-color: #f0f0f0 !important;
  color: #999999 !important;
  cursor: not-allowed !important;
  border: 1px solid #dddddd !important;
}
</style>
