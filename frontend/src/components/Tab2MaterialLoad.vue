<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, watchEffect } from 'vue'
import { ElMessage } from 'element-plus'
import { getReferenceLocations, resolveWindParams } from '../api/scaffold.js'

const props = defineProps({
  form: {
    type: Object,
    required: true
  }
})

const roughnessOptions = [
  { value: 'A', label: 'A类（近海海面、海岛）' },
  { value: 'B', label: 'B类（田野、乡村、丛林、丘陵）' },
  { value: 'C', label: 'C类（有密集建筑群的城市郊区）' },
  { value: 'D', label: 'D类（有密集建筑群的城市市区）' }
]

const constructionLoadOptions = [
  { value: 1.0, label: '1.0 防护脚手架' },
  { value: 2.0, label: '2.0 装修脚手架' },
  { value: 3.0, label: '3.0 砌筑作业脚手架' }
]

const windShapeFactorOptions = [
  { value: 1.0, label: '1.0 建筑墙体已砌筑' },
  { value: 1.3, label: '1.3 建筑墙体未砌筑' }
]

const wallTieConnectionOptions = [
  { value: 'anchor_bolt', label: '预埋螺栓式' },
  { value: 'embedded_tube', label: '预埋短钢管式' },
  { value: 'clamp_column', label: '钢管抱柱式' }
]

const wallTieTubeSpecOptions = [
  { value: 'Φ48×3.25', label: 'Φ48×3.25' },
  { value: 'Φ48×2.75', label: 'Φ48×2.75' }
]

const wallTieFastenerOptions = [
  { value: 'DOUBLE', label: '双扣件' },
  { value: 'SINGLE', label: '单扣件' }
]

const wallTieBoltDiameterOptions = [16, 18, 20, 22, 24]

const wallTieConcreteGradeOptions = ['C20', 'C25', 'C30', 'C35', 'C40']

const verticalTubeOptions = [
  { value: 'standard_b', label: '标准型（B型）' },
  { value: 'heavy_z', label: '重型（Z型）' }
]

const foundationHardenedOptions = [
  { value: 'yes', label: '是' },
  { value: 'no', label: '否' }
]

const adjustableBaseTypeOptions = [
  { value: 'B', label: 'B型 100kN' },
  { value: 'Z', label: 'Z型 140kN' }
]

const soilBearingDefaults = {
  COMPACTED_FILL: 120,
  CLAY: 180,
  SILT: 130,
  SAND: 160,
  WEATHERED_ROCK: 300,
  OTHER: 120
}

const verticalTubeModelMapping = {
  standard_b: {
    pole_model: 'B-LG-300',
    ledger_model: 'B-SG',
    brace_model: 'B-XG'
  },
  heavy_z: {
    pole_model: 'Z-LG-300',
    ledger_model: 'Z-SG',
    brace_model: 'Z-XG'
  }
}

function normalizeVerticalTubeSpec(value) {
  const legacyMapping = {
    Q355_PHI48X3_25: 'standard_b',
    Q355_PHI48X3_0: 'standard_b',
    Q235_PHI48X3_25: 'standard_b'
  }

  if (verticalTubeOptions.some((item) => item.value === value)) {
    return value
  }

  return legacyMapping[value] ?? 'standard_b'
}

function syncComponentModelsByVerticalType(verticalType) {
  const normalizedType = normalizeVerticalTubeSpec(verticalType)
  const modelConfig =
    verticalTubeModelMapping[normalizedType] ?? verticalTubeModelMapping.standard_b

  props.form.material_load_params.pole_model = modelConfig.pole_model
  props.form.material_load_params.ledger_model = modelConfig.ledger_model
  props.form.material_load_params.brace_model = modelConfig.brace_model
}

const cascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
  checkStrictly: false
}

const locationOptions = ref([])
const locationLoading = ref(false)
const locationResolving = ref(false)
const locationSelection = ref([])
const resolvedAltitudeM = ref(null)

let resolveTimerId = 0
let resolveRequestSerial = 0

const windLoad = computed(() => {
  const w0 = Number(props.form.material_load_params.basic_wind_pressure_w0_kn_m2 || 0)
  const muz = Number(props.form.material_load_params.wind_height_factor_muz || 0)
  const us = Number(props.form.material_load_params.wind_shape_factor || 0)
  return w0 * muz * us
})

function normalizeWallTieConnectionType(value) {
  const legacyMapping = {
    EXPANSION_BOLT: 'anchor_bolt',
    CHEMICAL_BOLT: 'anchor_bolt',
    EMBEDDED: 'embedded_tube'
  }

  if (wallTieConnectionOptions.some((item) => item.value === value)) {
    return value
  }

  return legacyMapping[value] ?? 'anchor_bolt'
}

function normalizeWallTieTubeSpec(value) {
  const normalizedValue = String(value || '').replace(/\s+/g, '')
  const legacyMapping = {
    'Φ48×3.2': 'Φ48×3.25',
    'Φ48.3×3.2': 'Φ48×3.25',
    'Φ48.3×3.25': 'Φ48×3.25',
    'Φ48.3×2.75': 'Φ48×2.75'
  }

  if (wallTieTubeSpecOptions.some((item) => item.value === normalizedValue)) {
    return normalizedValue
  }

  return legacyMapping[normalizedValue] ?? 'Φ48×3.25'
}

function normalizeFastenerType(value) {
  if (wallTieFastenerOptions.some((item) => item.value === value)) {
    return value
  }

  return value === '单扣件' ? 'SINGLE' : 'DOUBLE'
}

function normalizeBoltDiameter(value) {
  const numericValue = Number(value)
  return wallTieBoltDiameterOptions.includes(numericValue) ? numericValue : 18
}

function normalizeConcreteGrade(value) {
  return wallTieConcreteGradeOptions.includes(value) ? value : 'C30'
}

function getBoltStrengthByDiameter(diameter) {
  const mapping = {
    16: 170,
    18: 170,
    20: 170,
    22: 170,
    24: 170
  }

  return mapping[Number(diameter)] ?? 170
}

function getBondStrengthByConcreteGrade(grade) {
  // 前端临时回填值，按当前业务约定填写，后续可按正式规范条文复核调整。
  const mapping = {
    C20: 1.0,
    C25: 1.2,
    C30: 1.5,
    C35: 1.5,
    C40: 1.5
  }

  return mapping[grade] ?? 1.5
}

function normalizeFoundationHardened(value) {
  return value === 'no' ? 'no' : 'yes'
}

function normalizeAdjustableBaseType(value) {
  return value === 'Z' ? 'Z' : 'B'
}

function normalizeSoilType(value) {
  return Object.prototype.hasOwnProperty.call(soilBearingDefaults, value)
    ? value
    : 'COMPACTED_FILL'
}

function getSoilBearingDefault(soilType) {
  return soilBearingDefaults[normalizeSoilType(soilType)] ?? 120
}

function getFoundationBasePlateArea(foundHardened) {
  return normalizeFoundationHardened(foundHardened) === 'yes' ? 0.25 : 0.15 * 0.15
}

function getAdjustableBaseCapacityByType(baseType) {
  return normalizeAdjustableBaseType(baseType) === 'Z' ? 140 : 100
}

function ensureFoundationParamDefaults() {
  const params = props.form.foundation_params
  if (!params) {
    return
  }

  params.foundation_hardened = normalizeFoundationHardened(params.foundation_hardened)
  params.adjustable_base_type = normalizeAdjustableBaseType(params.adjustable_base_type)
  params.soil_type = normalizeSoilType(params.soil_type)

  if (
    params.bearing_capacity_fg_kpa === undefined ||
    params.bearing_capacity_fg_kpa === null ||
    params.bearing_capacity_fg_kpa === ''
  ) {
    params.bearing_capacity_fg_kpa = getSoilBearingDefault(params.soil_type)
  }

  params.base_plate_area_m2 = getFoundationBasePlateArea(params.foundation_hardened)
  params.adjustable_base_capacity_kn = getAdjustableBaseCapacityByType(
    params.adjustable_base_type
  )
}

const wallTieConnectionType = computed(
  () => props.form.wall_tie_params.wall_tie_connection_type ?? 'anchor_bolt'
)

const isAnchorBoltConnection = computed(
  () => wallTieConnectionType.value === 'anchor_bolt'
)

const isEmbeddedTubeConnection = computed(
  () => wallTieConnectionType.value === 'embedded_tube'
)

const isClampColumnConnection = computed(
  () => wallTieConnectionType.value === 'clamp_column'
)

const showWallTieFastenerField = computed(
  () => isEmbeddedTubeConnection.value || isClampColumnConnection.value
)

const showWallTieTubeSpecField = computed(
  () =>
    isAnchorBoltConnection.value ||
    isEmbeddedTubeConnection.value ||
    isClampColumnConnection.value
)

const showWallTieConcreteField = computed(
  () => isAnchorBoltConnection.value || isEmbeddedTubeConnection.value
)

const wallTieTubeSpecLabel = computed(() =>
  isAnchorBoltConnection.value ? '连墙件钢管规格' : '钢管规格'
)

const wallTieAnchorDepthLabel = computed(() =>
  isEmbeddedTubeConnection.value ? '预埋深度 l(mm)' : '锚固深度 l(mm)'
)

const boltStrength = computed(() =>
  getBoltStrengthByDiameter(props.form.wall_tie_params.bolt_diameter_mm)
)

const bondStrength = computed(() => {
  return getBondStrengthByConcreteGrade(props.form.wall_tie_params.concrete_grade)
})

const hasCompleteLocation = computed(() => {
  return Boolean(
    props.form.location_info?.province &&
      props.form.location_info?.city
  )
})

const autoFillStatusText = computed(() => {
  if (locationResolving.value) {
    return '正在根据项目所在地、地面粗糙度和搭设高度自动回填风参数…'
  }

  if (hasCompleteLocation.value && resolvedAltitudeM.value !== null) {
    return ''
  }

  return '选择省市后，将自动回填基本风压 ω0、城市海拔和风压高度变化系数 μz。'
})

function buildLocationOptions(provinces) {
  return provinces.map((province) => ({
    value: province.name,
    label: province.name,
    children: (province.cities || []).map((city) => ({
      value: city.name,
      label: city.name
    }))
  }))
}

function syncLocationSelectionFromForm() {
  if (props.form.location_info?.province && props.form.location_info?.city) {
    locationSelection.value = [
      props.form.location_info.province,
      props.form.location_info.city
    ]
    return
  }

  locationSelection.value = []
}

function clearResolveTimer() {
  if (resolveTimerId) {
    window.clearTimeout(resolveTimerId)
    resolveTimerId = 0
  }
}

function queueResolveWindParams() {
  clearResolveTimer()

  if (!hasCompleteLocation.value) {
    return
  }

  const height = Number(props.form.geometry_params.erection_height_hs_m || 0)
  if (height <= 0) {
    return
  }

  resolveTimerId = window.setTimeout(() => {
    resolveTimerId = 0
    handleResolveWindParams()
  }, 250)
}

async function fetchLocationOptions() {
  locationLoading.value = true

  try {
    const { data } = await getReferenceLocations()
    locationOptions.value = buildLocationOptions(data?.provinces || [])
    syncLocationSelectionFromForm()

    if (hasCompleteLocation.value) {
      queueResolveWindParams()
    }
  } catch (error) {
    console.error('获取省市级联数据失败', error)
    ElMessage.error('省市参考数据加载失败，请确认后端参考接口已启动。')
  } finally {
    locationLoading.value = false
  }
}

async function handleResolveWindParams() {
  if (!hasCompleteLocation.value) {
    return
  }

  const height = Number(props.form.geometry_params.erection_height_hs_m || 0)
  const roughness = props.form.material_load_params.terrain_roughness_category
  if (height <= 0 || !roughness) {
    return
  }

  const currentSerial = ++resolveRequestSerial
  locationResolving.value = true

  try {
    const { data } = await resolveWindParams({
      province: props.form.location_info.province,
      city: props.form.location_info.city,
      roughness,
      erection_height_hs_m: height
    })

    if (currentSerial !== resolveRequestSerial) {
      return
    }

    props.form.material_load_params.basic_wind_pressure_w0_kn_m2 = Number(data.w0_kn_m2)
    props.form.material_load_params.wind_height_factor_muz = Number(data.wind_height_factor_muz)
    resolvedAltitudeM.value = Number(data.altitude_m)
  } catch (error) {
    if (currentSerial !== resolveRequestSerial) {
      return
    }

    console.error('自动解析风参数失败', error)
    const detail = error?.response?.data?.detail
    ElMessage.error(
      typeof detail === 'string' && detail.trim()
        ? detail.trim()
        : '风参数自动回填失败，请检查项目所在地信息。'
    )
  } finally {
    if (currentSerial === resolveRequestSerial) {
      locationResolving.value = false
    }
  }
}

function ensureWallTieParamDefaults(forceReset = false) {
  const params = props.form.wall_tie_params
  if (!params) {
    return
  }

  const connectionType = normalizeWallTieConnectionType(
    params.wall_tie_connection_type ?? params.connection_type
  )
  params.wall_tie_connection_type = connectionType

  if (forceReset || !params.bolt_diameter_mm) {
    params.bolt_diameter_mm = 18
  }
  params.bolt_diameter_mm = normalizeBoltDiameter(params.bolt_diameter_mm)

  if (forceReset || !params.concrete_grade) {
    params.concrete_grade = 'C30'
  }
  params.concrete_grade = normalizeConcreteGrade(params.concrete_grade)

  if (forceReset || !params.wall_tie_tube_spec) {
    params.wall_tie_tube_spec = normalizeWallTieTubeSpec(params.model)
  }
  params.wall_tie_tube_spec = normalizeWallTieTubeSpec(params.wall_tie_tube_spec)

  if (forceReset || !params.fastener_type) {
    params.fastener_type = 'DOUBLE'
  }
  params.fastener_type = normalizeFastenerType(params.fastener_type)

  if (forceReset || !params.calculation_length_l0_mm) {
    params.calculation_length_l0_mm = 1500
  }

  if (connectionType === 'anchor_bolt') {
    if (forceReset || !params.anchor_depth_mm) {
      params.anchor_depth_mm = 150
    }
  } else if (connectionType === 'embedded_tube') {
    if (forceReset || !params.anchor_depth_mm) {
      params.anchor_depth_mm = 200
    }
  } else if (forceReset && !params.anchor_depth_mm) {
    params.anchor_depth_mm = 200
  }

  params.bolt_tensile_strength_n_mm2 = getBoltStrengthByDiameter(params.bolt_diameter_mm)
  params.allowable_bond_strength_n_mm2 = getBondStrengthByConcreteGrade(params.concrete_grade)

  params.connection_type = connectionType
  params.bolt_diameter_d_mm = params.bolt_diameter_mm
  params.fastener_connection_type = params.fastener_type
  params.model = params.wall_tie_tube_spec
  params.section_type = 'TUBE'
}

watch(
  locationSelection,
  (value) => {
    if (Array.isArray(value) && value.length === 2) {
      props.form.location_info.province = value[0]
      props.form.location_info.city = value[1]
      queueResolveWindParams()
      return
    }

    props.form.location_info.province = ''
    props.form.location_info.city = ''
    resolvedAltitudeM.value = null
  },
  { deep: true }
)

watch(
  () => [
    props.form.geometry_params.erection_height_hs_m,
    props.form.material_load_params.terrain_roughness_category
  ],
  () => {
    if (hasCompleteLocation.value) {
      queueResolveWindParams()
    }
  }
)

watch(
  () => props.form.wall_tie_params.wall_tie_connection_type,
  (value) => {
    const normalizedType = normalizeWallTieConnectionType(
      value ?? props.form.wall_tie_params.connection_type
    )

    if (props.form.wall_tie_params.wall_tie_connection_type !== normalizedType) {
      props.form.wall_tie_params.wall_tie_connection_type = normalizedType
      return
    }

    ensureWallTieParamDefaults(true)
  }
)

watch(
  () => props.form.foundation_params.soil_type,
  (value) => {
    const normalizedSoilType = normalizeSoilType(value)

    if (props.form.foundation_params.soil_type !== normalizedSoilType) {
      props.form.foundation_params.soil_type = normalizedSoilType
      return
    }

    props.form.foundation_params.bearing_capacity_fg_kpa = getSoilBearingDefault(
      normalizedSoilType
    )
  },
  { immediate: true }
)

watchEffect(() => {
  const normalizedVerticalTubeSpec = normalizeVerticalTubeSpec(
    props.form.material_load_params.vertical_tube_spec
  )

  if (props.form.material_load_params.vertical_tube_spec !== normalizedVerticalTubeSpec) {
    props.form.material_load_params.vertical_tube_spec = normalizedVerticalTubeSpec
  }

  syncComponentModelsByVerticalType(normalizedVerticalTubeSpec)

  ensureWallTieParamDefaults()
  ensureFoundationParamDefaults()
})

onMounted(() => {
  fetchLocationOptions()
})

onBeforeUnmount(() => {
  clearResolveTimer()
})
</script>

<template>
  <div class="tab-pane">
    <div class="section-title">材料参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>盘扣立杆类型</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.vertical_tube_spec">
              <option
                v-for="item in verticalTubeOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
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
      <div class="field field--full">
        <label>项目所在地</label>
        <el-cascader
          v-model="locationSelection"
          class="location-cascader"
          :options="locationOptions"
          :props="cascaderProps"
          :disabled="locationLoading"
          clearable
          filterable
          :show-all-levels="true"
          separator=" / "
          placeholder="请选择省份 / 城市"
        />
      </div>

      <div v-if="autoFillStatusText" class="field field--full field--hint">
        <span>{{ autoFillStatusText }}</span>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>施工活荷载 Qkjj(kN/m²)</label>
          <div class="select-wrapper">
            <select v-model.number="form.material_load_params.construction_live_load_kn_m2">
              <option
                v-for="item in constructionLoadOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>作业层数 njj</label>
          <input v-model.number="form.material_load_params.working_layer_count" type="number" step="1">
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>基本风压 ω0(kN/m²)</label>
          <input
            v-model.number="form.material_load_params.basic_wind_pressure_w0_kn_m2"
            type="number"
            step="0.01"
            readonly
            class="readonly-input"
          >
        </div>
        <div class="field">
          <label>城市海拔(m)</label>
          <input
            :value="resolvedAltitudeM === null ? '' : resolvedAltitudeM.toFixed(1)"
            type="text"
            readonly
            class="readonly-input"
          >
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>地面粗糙度</label>
          <div class="select-wrapper">
            <select v-model="form.material_load_params.terrain_roughness_category">
              <option
                v-for="item in roughnessOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>风压高度变化系数 μz</label>
          <input
            v-model.number="form.material_load_params.wind_height_factor_muz"
            type="number"
            step="0.001"
            readonly
            class="readonly-input"
          >
        </div>
      </div>

      <div class="form-row-2col">
        <div class="field">
          <label>风荷载体型系数 μs</label>
          <div class="select-wrapper">
            <select v-model.number="form.material_load_params.wind_shape_factor">
              <option
                v-for="item in windShapeFactorOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>风荷载标准值 ωk</label>
          <input :value="`${windLoad.toFixed(3)} kN/m²`" type="text" readonly class="readonly-input">
        </div>
      </div>
    </div>

    <div class="section-title">连墙件参数</div>
    <div class="form-section">
      <div :class="showWallTieFastenerField ? 'form-row-2col' : 'form-row-1col'">
        <div class="field">
          <label>连接方式</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.wall_tie_connection_type">
              <option
                v-for="item in wallTieConnectionOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div v-if="showWallTieFastenerField" class="field">
          <label>扣件连接</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.fastener_type">
              <option
                v-for="item in wallTieFastenerOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <div
        v-if="isAnchorBoltConnection"
        class="form-row-2col"
      >
        <div class="field">
          <label>螺栓直径 d(mm)</label>
          <div class="select-wrapper">
            <select v-model.number="form.wall_tie_params.bolt_diameter_mm">
              <option
                v-for="item in wallTieBoltDiameterOptions"
                :key="item"
                :value="item"
              >
                {{ item }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>螺栓抗拉强度(N/mm²)</label>
          <input
            :value="`${boltStrength} N/mm²`"
            type="text"
            readonly
            class="readonly-input"
          >
        </div>
      </div>

      <div
        v-if="showWallTieTubeSpecField"
        :class="isClampColumnConnection ? 'form-row-2col' : 'form-row-1col'"
      >
        <div class="field">
          <label>{{ wallTieTubeSpecLabel }}</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.wall_tie_tube_spec">
              <option
                v-for="item in wallTieTubeSpecOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div v-if="isClampColumnConnection" class="field">
          <label>计算长度 l0(mm)</label>
          <input v-model.number="form.wall_tie_params.calculation_length_l0_mm" type="number" step="1">
        </div>
      </div>

      <div
        v-if="showWallTieConcreteField"
        class="form-row-2col"
      >
        <div class="field">
          <label>混凝土强度等级</label>
          <div class="select-wrapper">
            <select v-model="form.wall_tie_params.concrete_grade">
              <option
                v-for="item in wallTieConcreteGradeOptions"
                :key="item"
                :value="item"
              >
                {{ item }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>容许粘结强度(N/mm²)</label>
          <input
            :value="`${bondStrength.toFixed(1)} N/mm²`"
            type="text"
            readonly
            class="readonly-input"
          >
        </div>
      </div>

      <div
        v-if="isAnchorBoltConnection || isEmbeddedTubeConnection"
        class="form-row-2col"
      >
        <div class="field">
          <label>{{ wallTieAnchorDepthLabel }}</label>
          <input v-model.number="form.wall_tie_params.anchor_depth_mm" type="number" step="1">
        </div>
        <div class="field">
          <label>计算长度 l0(mm)</label>
          <input v-model.number="form.wall_tie_params.calculation_length_l0_mm" type="number" step="1">
        </div>
      </div>
    </div>

    <div class="section-title">地基基础参数</div>
    <div class="form-section">
      <div class="form-row-2col">
        <div class="field">
          <label>外架基础是否硬化</label>
          <div class="select-wrapper">
            <select v-model="form.foundation_params.foundation_hardened">
              <option
                v-for="item in foundationHardenedOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>可调底座类型</label>
          <div class="select-wrapper">
            <select v-model="form.foundation_params.adjustable_base_type">
              <option
                v-for="item in adjustableBaseTypeOptions"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
      </div>

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
          <div class="field-note">
            地基承载力特征值仅供参考，实际请依据本项目工程地质勘察报告填写
          </div>
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

.form-row-1col {
  display: grid;
  grid-template-columns: 1fr;
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

.field--full {
  width: 100%;
}

.field--hint {
  margin-top: -2px;
  color: #7b8794;
  font-size: 12px;
  line-height: 1.4;
}

.field label {
  font-size: 12px;
  color: #666666;
}

.field-note {
  color: #999999;
  font-size: 12px;
  line-height: 1.4;
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

.location-cascader {
  width: 100%;
}

.location-cascader :deep(.el-input__wrapper) {
  min-height: 30px;
  border-radius: 5px;
  box-shadow: 0 0 0 1px #cccccc inset;
}

.location-cascader :deep(.el-input__inner) {
  font-size: 13px;
  color: #333333;
}

.readonly-input,
.field input[readonly] {
  background-color: #f0f0f0 !important;
  color: #999999 !important;
  cursor: not-allowed !important;
  border: 1px solid #dddddd !important;
}
</style>
