<script setup>
import { computed, ref } from 'vue'
import { getReportUrl } from '../api/scaffold.js'
import NavBar from '../components/NavBar.vue'

const specs = [
  {
    code: 'JGJ/T 231',
    name: '盘扣式钢管脚手架技术标准',
    filename: 'JGJ T231-202-建筑施工承插型盘扣式钢管脚手架安全技术标准.pdf'
  },
  {
    code: 'JGJ 130',
    name: '扣件式钢管脚手架安全技术规范',
    filename: 'JGJ130-2011-建筑施工扣件式钢管脚手架安全技术规范.pdf'
  },
  {
    code: 'JGT 503',
    name: '承插型盘扣式钢管支架构件',
    filename: 'JGT 503-2016 承插型盘扣式钢管支架构件.pdf'
  },
  {
    code: 'GB 50007',
    name: '建筑地基基础设计规范',
    filename: 'GB50007-2011-建筑地基基础设计规范.pdf'
  },
  {
    code: 'GB 50009',
    name: '建筑结构荷载规范',
    filename: 'GB50009-2012-建筑结构荷载规范.pdf'
  },
  {
    code: 'GB 50010',
    name: '混凝土结构设计规范',
    filename: 'GB50010-2010-混凝土结构设计规范(2015年版）.pdf'
  },
  {
    code: 'GB 50017',
    name: '钢结构设计标准',
    filename: 'GB50017-2017-钢结构设计标准（含条文说明）.pdf'
  },
  {
    code: 'GB 50018',
    name: '冷弯薄壁型钢结构技术规范',
    filename: 'GB50018-2002-冷弯薄壁型钢结构技术规范.pdf'
  },
  {
    code: 'GB 50068',
    name: '建筑结构可靠性统一标准',
    filename: 'GB50068-2018-建筑结构可靠性设计统一标准.pdf'
  }
]

const activeIndex = ref(0)
const activeSpec = computed(() => specs[activeIndex.value])
const activePdfUrl = computed(() => {
  const filename = encodeURIComponent(activeSpec.value.filename)
  return getReportUrl(`/specs-files/${filename}`)
})

function selectSpec(index) {
  activeIndex.value = index
}

function downloadActiveSpec() {
  window.open(activePdfUrl.value)
}
</script>

<template>
  <div class="specs-page">
    <NavBar />
    <main class="specs-body">
      <aside class="specs-sidebar">
        <h2>规范文件</h2>
        <div class="specs-list">
          <button
            v-for="(spec, index) in specs"
            :key="spec.filename"
            type="button"
            class="specs-list__item"
            :class="{ 'is-active': activeIndex === index }"
            @click="selectSpec(index)"
          >
            <span class="specs-list__code">{{ spec.code }}</span>
            <span class="specs-list__name">{{ spec.name }}</span>
          </button>
        </div>
      </aside>

      <section class="specs-preview">
        <div class="specs-preview__header">
          <div>
            <h1>{{ activeSpec.code }}</h1>
            <p>{{ activeSpec.name }}</p>
          </div>
          <button type="button" class="download-button" @click="downloadActiveSpec">
            下载原文
          </button>
        </div>
        <iframe class="pdf-frame" :src="activePdfUrl" :title="activeSpec.name"></iframe>
      </section>
    </main>
  </div>
</template>

<style scoped>
.specs-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.specs-body {
  flex: 1;
  min-height: 0;
  display: flex;
}

.specs-sidebar {
  width: 240px;
  flex: 0 0 240px;
  padding: 16px 12px;
  box-sizing: border-box;
  border-right: 1px solid #e0e0e0;
  background: #ffffff;
}

.specs-sidebar h2 {
  margin: 0 0 12px;
  color: #2f3440;
  font-size: 16px;
  font-weight: 700;
}

.specs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.specs-list__item {
  width: 100%;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #4b5563;
  text-align: left;
  cursor: pointer;
}

.specs-list__item.is-active {
  border-color: #185fa5;
  background: #eaf3ff;
  color: #185fa5;
}

.specs-list__code {
  font-size: 13px;
  font-weight: 700;
}

.specs-list__name {
  font-size: 12px;
  line-height: 1.4;
}

.specs-preview {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 14px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.specs-preview__header {
  flex-shrink: 0;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 12px;
  background: #ffffff;
}

.specs-preview__header h1 {
  margin: 0;
  color: #2f3440;
  font-size: 18px;
  font-weight: 700;
}

.specs-preview__header p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.download-button {
  flex-shrink: 0;
  border: none;
  border-radius: 6px;
  padding: 8px 14px;
  background: #185fa5;
  color: #ffffff;
  font-size: 13px;
  cursor: pointer;
}

.pdf-frame {
  flex: 1;
  width: 100%;
  min-height: 0;
  border: none;
  border-radius: 12px;
  background: #ffffff;
}
</style>
