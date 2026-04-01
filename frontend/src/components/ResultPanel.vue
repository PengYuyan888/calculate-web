<script setup>
import { computed } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  },
  reportUrl: {
    type: String,
    default: ''
  },
  requestError: {
    type: String,
    default: ''
  }
})

const summary = computed(() => props.result?.result_summary ?? null)
const issueList = computed(() => (Array.isArray(props.result?.issues) ? props.result.issues : []))
const maxUtilization = computed(() => Number(summary.value?.max_utilization_ratio ?? 0))
const hasFailedResult = computed(() => props.result?.status === 'failed')
const showFailureDetails = computed(() => Boolean(props.requestError) || hasFailedResult.value)
const failureTitle = computed(() => (props.requestError ? '请求失败' : '验算未通过'))
const failureDescription = computed(() => {
  if (props.requestError) {
    return props.requestError
  }

  return props.result?.message || '请根据错误详情调整参数后重新验算。'
})

const metricCards = computed(() => [
  {
    key: 'utilization',
    label: '最大利用率',
    value: summary.value ? Number(summary.value.max_utilization_ratio ?? 0).toFixed(3) : '--',
    tone: summary.value && Number(summary.value.max_utilization_ratio ?? 0) > 0.9 ? '#854F0B' : '#222222',
    note: summary.value?.governing_check_item || '控制验算项'
  },
  {
    key: 'stress',
    label: '最大应力(MPa)',
    value: summary.value ? Number(summary.value.max_stress_mpa ?? 0).toFixed(2) : '--',
    tone: '#222222',
    note: '允许值 300.0 MPa'
  },
  {
    key: 'axial',
    label: '最大轴力(kN)',
    value: summary.value ? Number(summary.value.max_axial_force_kn ?? 0).toFixed(3) : '--',
    tone: '#222222',
    note: '立杆最大轴力'
  },
  {
    key: 'deflection',
    label: '最大挠度(mm)',
    value: summary.value ? Number(summary.value.max_deflection_mm ?? 0).toFixed(3) : '--',
    tone: '#3B6D11',
    note: '限值 6.0 mm'
  }
])

function hasIssue(matcher) {
  return issueList.value.some((issue) => matcher(issue.item_code || ''))
}

function progressColor(ratio) {
  if (ratio > 0.9) {
    return '#E24B4A'
  }
  if (ratio >= 0.7) {
    return '#BA7517'
  }
  return '#639922'
}

const checkCards = computed(() => {
  const ratioPercent = Math.min(Math.max(maxUtilization.value * 100, 0), 100)
  return [
    {
      key: 'horizontal',
      label: '横向横杆',
      passed: !hasIssue((code) =>
        [
          'HORIZONTAL_LEDGER_BENDING_EXCEEDED',
          'HORIZONTAL_LEDGER_DEFLECTION_EXCEEDED',
          'HORIZONTAL_LEDGER_SHEAR_EXCEEDED'
        ].includes(code)
      ),
      ratioPercent
    },
    {
      key: 'vertical',
      label: '立杆稳定',
      passed: !hasIssue((code) =>
        ['VERTICAL_STANDARD_SLENDERNESS_EXCEEDED', 'VERTICAL_STANDARD_STABILITY_EXCEEDED'].includes(code)
      ),
      ratioPercent
    },
    {
      key: 'wall',
      label: '连墙件',
      passed: !hasIssue((code) => code.startsWith('WALL_TIE_')),
      ratioPercent
    },
    {
      key: 'foundation',
      label: '地基基础',
      passed: !hasIssue((code) => code.startsWith('FOUNDATION_') || code.startsWith('ADJUSTABLE_BASE_')),
      ratioPercent
    }
  ]
})

const statusTag = computed(() => {
  if (!props.result) {
    return null
  }

  if (props.result.status === 'success') {
    return {
      text: '✓ 全部通过',
      background: '#EAF3DE',
      color: '#3B6D11'
    }
  }

  return {
    text: '✗ 存在不通过项',
    background: '#FCEBEB',
    color: '#A32D2D'
  }
})
</script>

<template>
  <section class="result-panel">
    <div class="metrics-row">
      <div
        v-for="card in metricCards"
        :key="card.key"
        class="metric-card"
        :class="{ 'is-loading': loading }"
      >
        <div class="metric-card__label">{{ card.label }}</div>
        <div class="metric-card__value" :style="{ color: card.tone }">
          {{ loading ? '' : card.value }}
        </div>
        <div class="metric-card__note">{{ loading ? '' : card.note }}</div>
      </div>

      <div class="action-card" :class="{ 'is-empty': !result && !loading }">
        <template v-if="loading">
          <div class="action-skeleton"></div>
          <div class="action-skeleton action-skeleton--button"></div>
        </template>

        <template v-else-if="result">
          <span
            v-if="statusTag"
            class="status-tag"
            :style="{ background: statusTag.background, color: statusTag.color }"
          >
            {{ statusTag.text }}
          </span>

          <a
            v-if="reportUrl"
            :href="reportUrl"
            class="download-link"
            download
            target="_blank"
            rel="noopener noreferrer"
          >
            <button type="button" class="download-button">
              下载 Word 计算书
            </button>
          </a>
        </template>

        <template v-else>
          <div class="placeholder-text">填写参数后点击「开始验算」</div>
        </template>
      </div>
    </div>

    <div class="progress-row">
      <div
        v-for="item in checkCards"
        :key="item.key"
        class="progress-card"
      >
        <span class="progress-card__label">{{ item.label }}</span>
        <div class="progress-card__right">
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{
                width: result ? `${item.ratioPercent}%` : '0%',
                background: result ? progressColor(maxUtilization) : '#dddddd'
              }"
            ></div>
          </div>
          <span
            class="progress-status"
            :style="result ? {
              background: item.passed ? '#EAF3DE' : '#FCEBEB',
              color: item.passed ? '#3B6D11' : '#A32D2D'
            } : {}"
          >
            {{ result ? (item.passed ? '通过' : '不通过') : '待验算' }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="showFailureDetails" class="failure-panel">
      <div class="failure-panel__title">{{ failureTitle }}</div>
      <div class="failure-panel__message">{{ failureDescription }}</div>

      <div v-if="issueList.length" class="failure-panel__list">
        <div
          v-for="(issue, index) in issueList"
          :key="`${issue.item_code || issue.check_item}-${index}`"
          class="failure-panel__item"
        >
          <strong>{{ issue.check_item }}</strong>：{{ issue.message }}
          <div v-if="issue.suggestion" class="failure-panel__suggestion">建议：{{ issue.suggestion }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.result-panel {
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metrics-row {
  flex: 3;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) 120px;
  gap: 8px;
}

.metric-card,
.action-card,
.progress-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #ffffff;
}

.metric-card {
  min-width: 0;
  padding: 9px 11px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 4px;
}

.metric-card__label {
  font-size: 10px;
  color: #999999;
}

.metric-card__value {
  min-height: 20px;
  font-size: 16px;
  font-weight: 500;
}

.metric-card__note {
  min-height: 12px;
  font-size: 9px;
  color: #aaaaaa;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-card.is-loading {
  position: relative;
  overflow: hidden;
}

.metric-card.is-loading::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(240, 240, 240, 0.55), rgba(224, 224, 224, 0.9), rgba(240, 240, 240, 0.55));
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite linear;
}

.action-card {
  padding: 9px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.action-card.is-empty {
  align-items: center;
}

.placeholder-text {
  font-size: 10px;
  color: #999999;
  text-align: center;
  line-height: 1.5;
}

.status-tag {
  align-self: flex-start;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
}

.download-link {
  display: block;
  width: 100%;
}

.download-button {
  width: 100%;
  height: 26px;
  border: none;
  border-radius: 4px;
  background: #185fa5;
  color: #ffffff;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
}

.action-skeleton {
  height: 20px;
  border-radius: 6px;
  background: linear-gradient(90deg, #f0f0f0, #e2e2e2, #f0f0f0);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite linear;
}

.action-skeleton--button {
  height: 26px;
}

.progress-row {
  flex: 2;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
}

.progress-card {
  padding: 7px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.progress-card__label {
  font-size: 10px;
  color: #888888;
  white-space: nowrap;
}

.progress-card__right {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-track {
  width: 40px;
  height: 3px;
  border-radius: 999px;
  background: #dddddd;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
}

.progress-status {
  flex-shrink: 0;
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #f2f2f2;
  color: #999999;
}

.failure-panel {
  margin-top: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 3px solid #a32d2d;
  background: #fcebeb;
}

.failure-panel__title {
  font-size: 12px;
  font-weight: 600;
  color: #a32d2d;
}

.failure-panel__message {
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.6;
  color: #7b1f1f;
}

.failure-panel__list {
  margin-top: 8px;
}

.failure-panel__item {
  font-size: 11px;
  line-height: 1.6;
  color: #a32d2d;
}

.failure-panel__item + .failure-panel__item {
  margin-top: 6px;
}

.failure-panel__suggestion {
  color: #666666;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
