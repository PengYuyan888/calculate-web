<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteHistory, downloadReport, getHistoryDetail, getHistoryList } from '../api/scaffold.js'
import NavBar from '../components/NavBar.vue'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { isLoggedIn } = useAuth()

const historyTableRef = ref(null)
const loading = ref(false)
const historyList = ref([])
const selectedRows = ref([])
const batchDeleteLoading = ref(false)
const deletingRowIds = ref([])

function getErrorMessage(error, fallbackMessage) {
  const message = error?.response?.data?.message
  const detail = error?.response?.data?.detail

  if (typeof message === 'string' && message.trim()) {
    return message.trim()
  }

  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || JSON.stringify(item))
      .filter(Boolean)
      .join('；')
  }

  return fallbackMessage
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatScaffoldType(type) {
  if (type === 'RINGLOCK_DOUBLE_ROW_EXTERIOR') {
    return '盘扣式双排外脚手架'
  }

  return type || '-'
}

function formatStatus(status) {
  if (status === 'passed') {
    return '通过'
  }

  if (status === 'failed') {
    return '未通过'
  }

  return status || '-'
}

function getStatusText(row) {
  return row.status ? formatStatus(row.status) : row.overall_passed ? '通过' : '未通过'
}

function parseConstructionPart(requestSnapshot) {
  if (!requestSnapshot) {
    return '-'
  }

  try {
    const snapshot = JSON.parse(requestSnapshot)
    return snapshot?.basic_info?.construction_part || '-'
  } catch {
    return '-'
  }
}

async function fillConstructionParts(records) {
  const recordsWithPlaceholder = records.map((record) => ({
    ...record,
    construction_part: '-'
  }))
  historyList.value = recordsWithPlaceholder

  const details = await Promise.allSettled(
    recordsWithPlaceholder.map((record) => getHistoryDetail(record.id))
  )

  historyList.value = recordsWithPlaceholder.map((record, index) => {
    const detail = details[index]
    if (detail.status !== 'fulfilled') {
      return record
    }

    return {
      ...record,
      construction_part: parseConstructionPart(detail.value.data?.request_snapshot)
    }
  })
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

async function loadHistoryList() {
  if (!isLoggedIn.value) {
    router.push('/login')
    return
  }

  loading.value = true

  try {
    const res = await getHistoryList()
    const records = Array.isArray(res.data) ? res.data : []
    await fillConstructionParts(records)
    selectedRows.value = []
    await nextTick()
    historyTableRef.value?.clearSelection()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '历史记录加载失败'))
  } finally {
    loading.value = false
  }
}

async function downloadRecordReport(row) {
  if (!isLoggedIn.value) {
    router.push('/login')
    return
  }

  try {
    const res = await getHistoryDetail(row.id)
    const reportPath = res.data?.report_path

    if (!reportPath) {
      ElMessage.warning('该记录暂无计算书')
      return
    }

    downloadReport(reportPath)
    ElMessage.success('已开始下载计算书')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '计算书下载失败'))
  }
}

function isRowDeleting(recordId) {
  return deletingRowIds.value.includes(recordId)
}

function handleBatchDownload() {
  if (!selectedRows.value.length) {
    return
  }

  let downloadCount = 0
  let skippedCount = 0

  selectedRows.value.forEach((row) => {
    if (!row.report_path) {
      skippedCount += 1
      return
    }

    downloadReport(row.report_path)
    downloadCount += 1
  })

  if (skippedCount > 0) {
    ElMessage.warning(`已跳过 ${skippedCount} 条暂无计算书的记录`)
  }

  if (downloadCount > 0) {
    ElMessage.success(`已开始下载 ${downloadCount} 份计算书`)
  }
}

async function handleBatchDelete() {
  if (!selectedRows.value.length) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedRows.value.length} 条记录吗？删除后计算书文件将一并删除。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  batchDeleteLoading.value = true

  let successCount = 0
  let failureCount = 0

  try {
    for (const row of selectedRows.value) {
      try {
        await deleteHistory(row.id)
        successCount += 1
      } catch {
        failureCount += 1
      }
    }

    await loadHistoryList()

    if (failureCount === 0) {
      ElMessage.success(`已删除 ${successCount} 条记录`)
      return
    }

    if (successCount === 0) {
      ElMessage.error('批量删除失败，请稍后重试')
      return
    }

    ElMessage.warning(`已删除 ${successCount} 条记录，${failureCount} 条删除失败`)
  } finally {
    batchDeleteLoading.value = false
  }
}

async function handleDeleteRow(row) {
  try {
    await ElMessageBox.confirm(
      '确定删除该条记录吗？删除后计算书文件将一并删除。',
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  deletingRowIds.value = [...deletingRowIds.value, row.id]

  try {
    const res = await deleteHistory(row.id)
    historyList.value = historyList.value.filter((item) => item.id !== row.id)
    selectedRows.value = selectedRows.value.filter((item) => item.id !== row.id)
    ElMessage.success(res.data?.message || '删除成功')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除失败'))
  } finally {
    deletingRowIds.value = deletingRowIds.value.filter((id) => id !== row.id)
  }
}

onMounted(() => {
  loadHistoryList()
})
</script>

<template>
  <div class="history-page">
    <NavBar />
    <el-card class="history-card" shadow="never">
      <template #header>
        <div class="history-header">
          <div>
            <h1>历史记录</h1>
            <p>查看当前账号保存的脚手架验算结果</p>
          </div>
        </div>
      </template>

      <div class="history-toolbar">
        <el-button
          type="primary"
          :disabled="!selectedRows.length"
          @click="handleBatchDownload"
        >
          批量下载
        </el-button>
        <el-button
          type="danger"
          :disabled="!selectedRows.length"
          :loading="batchDeleteLoading"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
      </div>

      <el-table
        ref="historyTableRef"
        v-loading="loading"
        :data="historyList"
        :resizable="false"
        border
        stripe
        empty-text="暂无历史记录"
        class="history-table"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column type="index" label="序号" width="80" align="center" />
        <el-table-column prop="project_name" label="项目名称" min-width="180">
          <template #default="{ row }">
            {{ row.project_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="施工部位" min-width="150">
          <template #default="{ row }">
            {{ row.construction_part || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="脚手架类型" min-width="180">
          <template #default="{ row }">
            {{ formatScaffoldType(row.scaffold_type) }}
          </template>
        </el-table-column>
        <el-table-column label="验算状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.overall_passed ? 'success' : 'danger'">
              {{ getStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="验算时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <div class="history-actions">
              <el-button type="primary" link @click="downloadRecordReport(row)">下载计算书</el-button>
              <el-button
                type="danger"
                link
                :loading="isRowDeleting(row.id)"
                @click="handleDeleteRow(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.history-page {
  height: 100%;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.history-card {
  margin: 18px;
  border-radius: 12px;
}

.history-toolbar {
  margin-bottom: 12px;
  display: flex;
  gap: 10px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history-header h1 {
  margin: 0;
  color: #2f3440;
  font-size: 20px;
  font-weight: 700;
}

.history-header p {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.history-table {
  width: 100%;
}

.history-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

</style>
