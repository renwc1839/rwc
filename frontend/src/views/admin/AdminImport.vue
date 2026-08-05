<template>
  <div class="admin-import">
    <h2>数据导入</h2>

    <!-- Upload Area -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <span class="card-title">上传文件</span>
      </template>
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :accept="'.csv,.xlsx,.xls'"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p>将 CSV 或 Excel 文件拖放到此处</p>
          <p class="upload-hint">支持 .csv / .xlsx / .xls 格式，最大 10 MB</p>
        </div>
      </el-upload>
    </el-card>

    <!-- File Preview -->
    <el-card v-if="selectedFile" shadow="never" class="section-card">
      <template #header>
        <span class="card-title">文件预览</span>
      </template>
      <p class="file-info">
        文件名：<strong>{{ selectedFile.name }}</strong>（{{ formatSize(selectedFile.size) }}）
      </p>
      <p v-if="previewHeaders.length" class="field-info">
        识别字段：<el-tag
          v-for="h in previewHeaders"
          :key="h"
          :type="requiredFields.includes(h) ? 'danger' : 'info'"
          size="small"
          class="field-tag"
        >{{ h }}<span v-if="requiredFields.includes(h)">*</span></el-tag>
      </p>
      <el-table v-if="previewRows.length" :data="previewRows" border stripe size="small" max-height="240">
        <el-table-column
          v-for="h in previewHeaders"
          :key="h"
          :prop="h"
          :label="h"
          min-width="120"
          show-overflow-tooltip
        />
      </el-table>
      <el-alert
        v-if="missingRequired.length"
        :title="`缺少必填字段：${missingRequired.join('、')}`"
        type="error"
        :closable="false"
        show-icon
        class="field-alert"
      />
      <el-alert
        v-if="previewHeaders.length && !missingRequired.length"
        title="字段校验通过，可以开始导入"
        type="success"
        :closable="false"
        show-icon
        class="field-alert"
      />

      <el-button
        type="primary"
        :icon="Upload"
        :loading="importing"
        :disabled="missingRequired.length > 0"
        class="import-btn"
        @click="startImport"
      >
        {{ importing ? '导入中...' : '开始导入' }}
      </el-button>
    </el-card>

    <!-- Import Progress -->
    <el-card v-if="importing" shadow="never" class="section-card">
      <template #header>
        <span class="card-title">导入进度</span>
      </template>
      <el-progress
        :percentage="100"
        :status="importResult ? 'success' : undefined"
        :indeterminate="!importResult"
      />
      <p class="progress-text">
        {{ importResult ? '导入完成' : '正在处理数据...' }}
      </p>
    </el-card>

    <!-- Import Result -->
    <el-card v-if="importResult" shadow="never" class="section-card">
      <template #header>
        <span class="card-title">导入结果</span>
      </template>
      <el-row :gutter="20" class="result-row">
        <el-col :span="8">
          <el-statistic title="总计" :value="importResult.total_records" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="成功" :value="importResult.success_records">
            <template #suffix>
              <el-icon style="color: #67c23a"><CircleCheckFilled /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="失败" :value="importResult.failed_records">
            <template #suffix>
              <el-icon v-if="importResult.failed_records > 0" style="color: #f56c6c"><CircleCloseFilled /></el-icon>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <div v-if="importResult.inspection" class="inspection-section">
        <div class="inspection-header">
          <h4>上传后检测</h4>
          <el-tag :type="inspectionTagType(importResult.inspection.level)">
            {{ inspectionLabel(importResult.inspection.level) }}
          </el-tag>
        </div>
        <div class="inspection-grid">
          <div class="inspection-cell">
            <span>异常项</span>
            <strong>{{ importResult.inspection.summary.abnormal }}</strong>
          </div>
          <div class="inspection-cell">
            <span>API 成功</span>
            <strong>{{ importResult.inspection.summary.api_success }}</strong>
          </div>
          <div class="inspection-cell">
            <span>API 异常</span>
            <strong>{{ importResult.inspection.summary.api_failed }}</strong>
          </div>
          <div class="inspection-cell">
            <span>已跳过</span>
            <strong>{{ importResult.inspection.summary.api_skipped }}</strong>
          </div>
        </div>
        <el-table
          v-if="importResult.inspection.abnormal_items.length"
          :data="importResult.inspection.abnormal_items"
          border
          stripe
          size="small"
          max-height="220"
        >
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="type" label="类型" width="150" show-overflow-tooltip />
          <el-table-column prop="message" label="异常内容" show-overflow-tooltip />
          <el-table-column prop="level" label="等级" width="100">
            <template #default="{ row }">
              <el-tag :type="inspectionTagType(row.level)" size="small">
                {{ inspectionLabel(row.level) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-table
          v-if="importResult.inspection.api_checks.length"
          :data="importResult.inspection.api_checks"
          border
          stripe
          size="small"
          max-height="180"
          class="api-table"
        >
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="service" label="API" width="140" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="apiStatusTagType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="结果" show-overflow-tooltip />
        </el-table>
      </div>

      <!-- Error Details -->
      <div v-if="importResult.error_log && importResult.error_log.length" class="error-section">
        <h4>错误详情</h4>
        <el-table :data="importResult.error_log" border stripe size="small" max-height="300">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
        </el-table>
        <el-button
          v-if="importResult.id"
          type="warning"
          size="small"
          class="retry-btn"
          @click="retryImport"
        >
          重试失败记录
        </el-button>
      </div>
    </el-card>

    <!-- History -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="history-header">
          <span class="card-title">导入历史</span>
          <el-select
            v-model="historyFilter"
            placeholder="状态筛选"
            clearable
            size="small"
            style="width: 140px"
            @change="fetchHistory"
          >
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
      </template>
      <el-table :data="history" v-loading="historyLoading" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="source_name" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="source_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.source_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_records" label="总计" width="70" />
        <el-table-column prop="success_records" label="成功" width="70">
          <template #default="{ row }">
            <span style="color: #67c23a">{{ row.success_records }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="failed_records" label="失败" width="70">
          <template #default="{ row }">
            <span :style="{ color: row.failed_records > 0 ? '#f56c6c' : '#909399' }">
              {{ row.failed_records }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="检测" width="120">
          <template #default="{ row }">
            <el-tag :type="inspectionTagType(row.inspection_level || 'normal')" size="small">
              {{ inspectionLabel(row.inspection_level || 'normal') }}
              <span v-if="row.abnormal_count"> {{ row.abnormal_count }}</span>
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <el-button
              v-if="row.failed_records > 0 && (row.status === 'completed' || row.status === 'failed')"
              size="small"
              type="warning"
              @click="retryTask(row.id)"
            >重试</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="historyPage"
        :page-size="historyPageSize"
        :total="historyTotal"
        layout="total, prev, pager, next"
        class="pagination"
        @current-change="fetchHistory"
      />
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="导入详情" width="640px">
      <template v-if="detailTask">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ detailTask.id }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ detailTask.source_name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ detailTask.source_type }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(detailTask.status)" size="small">
              {{ statusLabel(detailTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总计">{{ detailTask.total_records }}</el-descriptions-item>
          <el-descriptions-item label="成功">{{ detailTask.success_records }}</el-descriptions-item>
          <el-descriptions-item label="失败">{{ detailTask.failed_records }}</el-descriptions-item>
          <el-descriptions-item label="检测">
            <el-tag :type="inspectionTagType(detailTask.inspection_level || 'normal')" size="small">
              {{ inspectionLabel(detailTask.inspection_level || 'normal') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ new Date(detailTask.created_at).toLocaleString() }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="detailTask.inspection" class="detail-errors">
          <h4>检测明细</h4>
          <div class="inspection-grid">
            <div class="inspection-cell">
              <span>异常项</span>
              <strong>{{ detailTask.inspection.summary.abnormal }}</strong>
            </div>
            <div class="inspection-cell">
              <span>API 成功</span>
              <strong>{{ detailTask.inspection.summary.api_success }}</strong>
            </div>
            <div class="inspection-cell">
              <span>API 异常</span>
              <strong>{{ detailTask.inspection.summary.api_failed }}</strong>
            </div>
            <div class="inspection-cell">
              <span>已跳过</span>
              <strong>{{ detailTask.inspection.summary.api_skipped }}</strong>
            </div>
          </div>
          <el-table
            v-if="detailTask.inspection.abnormal_items.length"
            :data="detailTask.inspection.abnormal_items"
            border
            stripe
            size="small"
            max-height="220"
          >
            <el-table-column prop="row" label="行号" width="80" />
            <el-table-column prop="type" label="类型" width="150" show-overflow-tooltip />
            <el-table-column prop="message" label="异常内容" show-overflow-tooltip />
            <el-table-column prop="level" label="等级" width="100">
              <template #default="{ row }">
                <el-tag :type="inspectionTagType(row.level)" size="small">
                  {{ inspectionLabel(row.level) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-if="detailTask.error_log && detailTask.error_log.length" class="detail-errors">
          <h4>错误记录</h4>
          <el-table :data="detailTask.error_log" border stripe size="small" max-height="240">
            <el-table-column prop="row" label="行号" width="80" />
            <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  UploadFilled,
  Upload,
  CircleCheckFilled,
  CircleCloseFilled,
} from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
import { adminService } from '@/services/admin'
import type { ImportResult, ImportTask, ImportTaskDetail } from '@/types/admin'

const REQUIRED_FIELDS = ['title', 'address', 'district', 'price_monthly']

const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const previewHeaders = ref<string[]>([])
const previewRows = ref<Record<string, string>[]>([])
const importing = ref(false)
const importResult = ref<ImportResult | null>(null)
const history = ref<ImportTask[]>([])
const historyLoading = ref(false)
const historyFilter = ref('')
const historyPage = ref(1)
const historyPageSize = ref(20)
const historyTotal = ref(0)
const detailVisible = ref(false)
const detailTask = ref<ImportTaskDetail | null>(null)

const requiredFields = REQUIRED_FIELDS

const missingRequired = computed(() => {
  return REQUIRED_FIELDS.filter((f) => !previewHeaders.value.includes(f))
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function statusTagType(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function inspectionTagType(level: string) {
  const map: Record<string, string> = {
    normal: 'success',
    notice: 'info',
    warning: 'warning',
    critical: 'danger',
  }
  return map[level] || 'info'
}

function inspectionLabel(level: string) {
  const map: Record<string, string> = {
    normal: '正常',
    notice: '提示',
    warning: '需复核',
    critical: '异常',
  }
  return map[level] || level
}

function apiStatusTagType(status: string) {
  const map: Record<string, string> = {
    success: 'success',
    skipped: 'info',
    warning: 'warning',
    failed: 'danger',
  }
  return map[status] || 'info'
}

async function handleFileChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  selectedFile.value = raw
  importResult.value = null

  // Generate preview
  const ext = raw.name.split('.').pop()?.toLowerCase()
  try {
    if (ext === 'csv') {
      const text = await raw.text()
      const lines = text.trim().split('\n')
      if (lines.length > 0) {
        previewHeaders.value = lines[0].split(',').map((h) => h.trim().toLowerCase())
        previewRows.value = lines.slice(1, Math.min(lines.length, 6)).map((line) => {
          const values = line.split(',')
          const row: Record<string, string> = {}
          previewHeaders.value.forEach((h, i) => {
            row[h] = (values[i] || '').trim()
          })
          return row
        })
      }
    } else {
      // Show preview from raw data for Excel (limited client-side)
      previewHeaders.value = [] // Excel preview requires server-side; just show filename
      previewRows.value = []
    }
  } catch {
    ElMessage.error('无法解析文件预览')
  }
}

function handleFileRemove() {
  selectedFile.value = null
  previewHeaders.value = []
  previewRows.value = []
  importResult.value = null
}

async function startImport() {
  if (!selectedFile.value) return
  importing.value = true
  importResult.value = null
  try {
    const result = await adminService.uploadImport(selectedFile.value)
    importResult.value = result
    ElMessage.success(`导入完成：成功 ${result.success_records} 条，失败 ${result.failed_records} 条`)
    fetchHistory()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

async function retryImport() {
  if (!importResult.value?.id) return
  try {
    const result = await adminService.retryImportTask(importResult.value.id)
    importResult.value = result
    ElMessage.success(`重试完成：成功补充 ${result.success_records} 条`)
    fetchHistory()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '重试失败')
  }
}

async function retryTask(taskId: number) {
  try {
    await adminService.retryImportTask(taskId)
    ElMessage.success('重试完成')
    fetchHistory()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '重试失败')
  }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const data = await adminService.getImportTasks({
      skip: (historyPage.value - 1) * historyPageSize.value,
      limit: historyPageSize.value,
      status: historyFilter.value || undefined,
    })
    history.value = data
    // Estimate total - we don't have a count endpoint but it's fine for now
    if (data.length < historyPageSize.value) {
      historyTotal.value = (historyPage.value - 1) * historyPageSize.value + data.length
    } else {
      historyTotal.value = historyPage.value * historyPageSize.value + 1
    }
  } catch {
    ElMessage.error('加载导入历史失败')
  } finally {
    historyLoading.value = false
  }
}

async function viewDetail(task: ImportTask) {
  try {
    detailTask.value = await adminService.getImportTaskDetail(task.id)
    detailVisible.value = true
  } catch {
    ElMessage.error('加载详情失败')
  }
}

// Auto-fetch on mount
import { onMounted } from 'vue'
onMounted(fetchHistory)
</script>

<style scoped>
.admin-import {
  max-width: 960px;
  margin: 0 auto;
}

.admin-import h2 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 24px;
}

.section-card {
  margin-bottom: 20px;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
}

.upload-area {
  width: 100%;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 12px;
}

.upload-text p {
  margin: 4px 0;
  color: #606266;
}

.upload-hint {
  font-size: 13px;
  color: #909399;
}

.file-info {
  margin-bottom: 12px;
  color: #606266;
}

.field-info {
  margin-bottom: 12px;
  line-height: 2;
}

.field-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}

.field-alert {
  margin-top: 12px;
}

.import-btn {
  margin-top: 16px;
}

.progress-text {
  margin-top: 12px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.result-row {
  margin-bottom: 8px;
}

.inspection-section {
  margin-top: 18px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}

.inspection-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.inspection-header h4 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.inspection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.inspection-cell {
  min-height: 64px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fff;
}

.inspection-cell span {
  display: block;
  margin-bottom: 6px;
  color: #909399;
  font-size: 12px;
}

.inspection-cell strong {
  color: #303133;
  font-size: 22px;
}

.api-table {
  margin-top: 12px;
}

.error-section {
  margin-top: 20px;
}

.error-section h4 {
  font-size: 14px;
  color: #f56c6c;
  margin-bottom: 10px;
}

.retry-btn {
  margin-top: 12px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 16px;
  justify-content: center;
}

.detail-errors {
  margin-top: 20px;
}

.detail-errors h4 {
  font-size: 14px;
  color: #f56c6c;
  margin-bottom: 10px;
}
</style>
