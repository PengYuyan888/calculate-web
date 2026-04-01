<script setup>
import { ref } from 'vue'
import Tab1BasicGeo from './Tab1BasicGeo.vue'
import Tab2MaterialLoad from './Tab2MaterialLoad.vue'

defineProps({
  form: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit'])
const activeTab = ref('basic')

function handleSubmit() {
  emit('submit')
}
</script>

<template>
  <aside class="left-panel">
    <div class="left-panel__tabs">
      <button
        type="button"
        class="left-panel__tab"
        :class="{ 'is-active': activeTab === 'basic' }"
        @click="activeTab = 'basic'"
      >
        <span>基本信息及</span>
        <span>架体几何参数</span>
      </button>
      <button
        type="button"
        class="left-panel__tab"
        :class="{ 'is-active': activeTab === 'material' }"
        @click="activeTab = 'material'"
      >
        <span>材料及</span>
        <span>荷载参数</span>
      </button>
    </div>

    <div class="left-panel__content form-content-area">
      <Tab1BasicGeo v-if="activeTab === 'basic'" :form="form" />
      <Tab2MaterialLoad v-else :form="form" />
    </div>

    <div class="left-panel__footer">
      <button
        type="button"
        class="submit-button"
        :disabled="loading"
        @click="handleSubmit"
      >
        {{ loading ? '验算中…' : '开始验算并生成计算书' }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
.left-panel {
  width: 290px;
  height: 100%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;
}

.left-panel__tabs {
  height: 46px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  flex-shrink: 0;
}

.left-panel__tab {
  border: none;
  border-bottom: 2px solid transparent;
  background: #f5f5f5;
  color: #999999;
  font-size: 11px;
  line-height: 1.2;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.left-panel__tab.is-active {
  background: #ffffff;
  color: #185fa5;
  border-bottom-color: #185fa5;
  font-weight: 500;
}

.left-panel__content,
.form-content-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.left-panel__footer {
  margin-top: auto;
  height: 56px;
  padding: 10px 14px;
  border-top: 1px solid #e0e0e0;
  background: #ffffff;
  flex-shrink: 0;
}

.submit-button {
  width: 100%;
  height: 34px;
  border: none;
  border-radius: 6px;
  background: #185fa5;
  color: #ffffff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.submit-button:disabled {
  opacity: 0.72;
  cursor: not-allowed;
}
</style>
