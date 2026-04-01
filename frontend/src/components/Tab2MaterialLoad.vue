<script setup>
import { computed, watchEffect } from 'vue'

const props = defineProps({
  form: {
    type: Object,
    required: true
  }
})

const windLoad = computed(() => {
  const w0 = Number(props.form.material_load_params.basic_wind_pressure_w0_kn_m2 || 0)
  const muz = Number(props.form.material_load_params.wind_height_factor_muz || 0)
  const us = Number(props.form.material_load_params.wind_shape_factor || 0)
  return w0 * muz * us
})

const boltStrength = computed(() => 170)

const bondStrength = computed(() => {
  const mapping = {
    C25: 1.3,
    C30: 1.5,
    C35: 1.6,
    C40: 1.8
  }
  return mapping[props.form.wall_tie_params.concrete_grade] ?? 1.5
})

const adjustableBaseCapacity = computed(() => {
  const mapping = {
    Q355_PHI48X3_25: 100,
    Q355_PHI48X3_0: 100,
    Q235_PHI48X3_25: 80
  }
  return mapping[props.form.material_load_params.vertical_tube_spec] ?? 100
})

watchEffect(() => {
  props.form.wall_tie_params.bolt_tensile_strength_n_mm2 = boltStrength.value
  props.form.wall_tie_params.allowable_bond_strength_n_mm2 = bondStrength.value
  props.form.foundation_params.adjustable_base_capacity_kn = adjustableBaseCapacity.value
})
</script>

<template>
  <div class="tab-pane">
    <div class="section-title">材料参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>立杆钢管规格</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.vertical_tube_spec">
              <option value="Q355_PHI48X3_25">Q355 Φ48×3.25</option>
              <option value="Q355_PHI48X3_0">Q355 Φ48×3.0</option>
              <option value="Q235_PHI48X3_25">Q235 Φ48×3.25</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>脚手板类型</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.plank_type">
              <option value="STEEL_PLANK">冲压钢脚手板</option>
              <option value="WOOD_PLANK">木脚手板</option>
              <option value="BAMBOO_PLANK">竹脚手板</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>脚手板铺设方式</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.plank_laying_method">
              <option value="1步1设">1步1设</option>
              <option value="隔步铺设">隔步铺设</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>单板宽度 b(mm)</label>
          <input v-model.number="form.material_load_params.single_plank_width_b_mm" type="number" step="1">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>脚手板自重 Gkjb(kN/m²)</label>
          <input v-model.number="form.material_load_params.plank_self_weight_kn_m2" type="number" step="0.01">
        </div>
        <div class="field">
          <label>安全网自重 Gkmw(kN/m²)</label>
          <input v-model.number="form.material_load_params.safety_net_self_weight_kn_m2" type="number" step="0.01">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>挡脚板类型</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.toe_board_type">
              <option value="木脚手板挡板">木脚手板挡板</option>
              <option value="钢挡板">钢挡板</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>挡脚板自重 Gkdb(kN/m)</label>
          <input v-model.number="form.material_load_params.toe_board_self_weight_kn_m" type="number" step="0.01">
        </div>
      </div>
    </div>

    <div class="section-title">荷载参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>施工活荷载 Qkjj(kN/m²)</label>
          <input v-model.number="form.material_load_params.construction_live_load_kn_m2" type="number" step="0.1">
        </div>
        <div class="field">
          <label>作业层数 njj</label>
          <input v-model.number="form.material_load_params.working_layer_count" type="number" step="1">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>基本风压 ω0(kN/m²)</label>
          <input v-model.number="form.material_load_params.basic_wind_pressure_w0_kn_m2" type="number" step="0.01">
        </div>
        <div class="field">
          <label>地面粗糙度</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.terrain_roughness_category">
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="D">D</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>风荷载体型系数 μs</label>
          <input v-model.number="form.material_load_params.wind_shape_factor" type="number" step="0.001">
        </div>
        <div class="field">
          <label>风压高度变化系数 μz</label>
          <input v-model.number="form.material_load_params.wind_height_factor_muz" type="number" step="0.001">
        </div>
      </div>

      <div class="field">
        <label>风荷载标准值 ωk</label>
        <input :value="`${windLoad.toFixed(3)} kN/m²`" type="text" readonly class="readonly-input">
      </div>
    </div>

    <div class="section-title">连墙件参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>连接方式</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.connection_type">
              <option value="EXPANSION_BOLT">膨胀螺栓</option>
              <option value="CHEMICAL_BOLT">化学螺栓</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>扣件连接</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.fastener_connection_type">
              <option value="DOUBLE">双扣件</option>
              <option value="SINGLE">单扣件</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>螺栓直径 d(mm)</label>
          <div class="select-wrapper">
            <select v-model.number="form.wall_tie_params.bolt_diameter_d_mm">
              <option :value="12">12</option>
              <option :value="14">14</option>
              <option :value="16">16</option>
              <option :value="18">18</option>
              <option :value="20">20</option>
              <option :value="22">22</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>螺栓抗拉强度</label>
          <input :value="`${boltStrength} N/mm²`" type="text" readonly class="readonly-input">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>混凝土强度等级</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.concrete_grade">
              <option value="C25">C25</option>
              <option value="C30">C30</option>
              <option value="C35">C35</option>
              <option value="C40">C40</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>容许粘结强度</label>
          <input :value="`${bondStrength.toFixed(1)} N/mm²`" type="text" readonly class="readonly-input">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>计算长度 l0(mm)</label>
          <input v-model.number="form.wall_tie_params.calculation_length_l0_mm" type="number" step="1">
        </div>
        <div class="field">
          <label>截面类型</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.section_type">
              <option value="TUBE">钢管</option>
              <option value="ANGLE">角钢</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="section-title">地基基础参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>地基土类型</label>
          <div class="select-wrapper">
            <select v-model="form.foundation_params.soil_type">
              <option value="COMPACTED_FILL">压实填土</option>
              <option value="CLAY">黏土</option>
              <option value="SILT">粉土</option>
              <option value="SAND">砂土</option>
              <option value="WEATHERED_ROCK">强风化岩</option>
              <option value="OTHER">其他</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>地基承载力特征值 fg(kPa)</label>
          <input v-model.number="form.foundation_params.bearing_capacity_fg_kpa" type="number" step="1">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>垫板底面积(m²)</label>
          <input v-model.number="form.foundation_params.sole_plate_area_m2" type="number" step="0.01">
        </div>
        <div class="field">
          <label>可调底座承载力</label>
          <input :value="`${adjustableBaseCapacity} kN`" type="text" readonly class="readonly-input">
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
