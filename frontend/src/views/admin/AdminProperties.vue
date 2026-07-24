<template>
  <div class="admin-properties" v-loading="loading">
    <h2>房源审核</h2>

    <el-input
      v-model="search"
      placeholder="搜索房源标题..."
      clearable
      class="search-box"
      @input="fetchProperties"
    />

    <el-table :data="filteredProperties" stripe style="width: 100%; margin-top: 16px">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="标题" min-width="220">
        <template #default="{ row }">
          <router-link
            class="property-title-link"
            :to="{ name: 'property-detail', params: { id: row.id } }"
            target="_blank"
          >
            {{ row.title }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="district" label="区域" width="100" />
      <el-table-column prop="price_monthly" label="月租" width="100">
        <template #default="{ row }">{{ row.price_monthly }} 元</template>
      </el-table-column>
      <el-table-column label="运营状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核结论" width="150">
        <template #default="{ row }">
          <el-select
            :model-value="auditMap[row.id]?.audit_status || '待复核'"
            size="small"
            @change="(val: string) => handleAuditChange(row, val)"
          >
            <el-option label="信息正常" value="信息正常" />
            <el-option label="信息异常" value="信息异常" />
            <el-option label="待复核" value="待复核" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="审核记录" min-width="170">
        <template #default="{ row }">
          <span class="audit-note">
            {{ auditMap[row.id]?.operator ? `${auditMap[row.id].operator} ${formatDateTime(auditMap[row.id].updated_at)}` : '未审核' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" width="120">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openProperty(row.id)">浏览</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminService } from '@/services/admin'
import { propertyService } from '@/services/property'
import type { Property, PropertyStatus } from '@/types/property'

const router = useRouter()
const route = useRoute()
const properties = ref<Property[]>([])
const auditMap = ref<Record<number, any>>({})
const loading = ref(false)
const search = ref('')

const statusLabels: Record<PropertyStatus, string> = {
  available: '可租',
  rented: '已租',
  maintenance: '维护中',
  offline: '已下架',
}

const countryKeywords: Record<string, string[]> = {
  英国: ['伦敦', '曼彻斯特', '伯明翰', '利物浦', '爱丁堡', '格拉斯哥', '布里斯托', '利兹', '谢菲尔德', '诺丁汉', 'London', 'Manchester', 'Birmingham', 'Liverpool', 'Edinburgh'],
  美国: ['纽约', '洛杉矶', '波士顿', '芝加哥', '西雅图', '旧金山', '华盛顿', '曼哈顿', 'New York', 'Los Angeles', 'Boston', 'Chicago', 'Seattle', 'San Francisco'],
  澳大利亚: ['悉尼', '墨尔本', '布里斯班', '阿德莱德', '珀斯', '堪培拉', 'Sydney', 'Melbourne', 'Brisbane', 'Adelaide', 'Perth'],
  加拿大: ['多伦多', '温哥华', '蒙特利尔', '渥太华', '滑铁卢', 'Toronto', 'Vancouver', 'Montreal', 'Ottawa', 'Waterloo'],
  新加坡: ['新加坡', 'Singapore'],
  日本: ['东京', '大阪', '京都', 'Tokyo', 'Osaka', 'Kyoto'],
  韩国: ['首尔', '釜山', 'Seoul', 'Busan'],
}

const filteredProperties = computed(() => {
  const q = search.value.toLowerCase()
  const country = typeof route.query.country === 'string' ? route.query.country : ''
  return properties.value.filter((p) => {
    const matchesSearch = !q || p.title.toLowerCase().includes(q) || p.district.toLowerCase().includes(q)
    const matchesCountry = !country || countryMatches(p.district, country)
    return matchesSearch && matchesCountry
  })
})

function countryMatches(district: string, country: string) {
  if (country === '其他国家/地区') {
    return !Object.values(countryKeywords).some((keywords) => keywords.some((keyword) => district.includes(keyword)))
  }
  return (countryKeywords[country] || []).some((keyword) => district.includes(keyword))
}

function applyRouteSearch() {
  search.value = typeof route.query.q === 'string' ? route.query.q : ''
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatDateTime(dateStr?: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { hour12: false })
}

function statusText(status: PropertyStatus) {
  return statusLabels[status] || status
}

function statusTag(status: PropertyStatus) {
  return ({
    available: 'success',
    rented: 'warning',
    maintenance: 'info',
    offline: 'danger',
  }[status] || 'info') as 'success' | 'warning' | 'info' | 'danger'
}

async function fetchProperties() {
  loading.value = true
  try {
    const [propertyList, audits] = await Promise.all([
      propertyService.list({ limit: 100 }),
      adminService.listPropertyAudits(),
    ])
    properties.value = propertyList
    auditMap.value = Object.fromEntries(audits.map((item) => [item.property_id, item]))
  } finally {
    loading.value = false
  }
}

async function handleAuditChange(property: Property, auditStatus: string) {
  try {
    const updated = await adminService.auditPropertyInfo(property.id, auditStatus)
    auditMap.value = { ...auditMap.value, [property.id]: updated }
    ElMessage.success('审核结论已记录，不影响房源运营状态')
  } catch {
    ElMessage.error('审核记录失败')
  }
}

function openProperty(propertyId: number) {
  const route = router.resolve({ name: 'property-detail', params: { id: String(propertyId) } })
  window.open(route.href, '_blank', 'noopener')
}

watch(() => route.query.q, applyRouteSearch)

onMounted(() => {
  applyRouteSearch()
  fetchProperties()
})
</script>

<style scoped>
.admin-properties {
  max-width: 1100px;
  margin: 0 auto;
}

.admin-properties h2 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 16px;
}

.search-box {
  max-width: 400px;
}

.property-title-link {
  color: #e66f3c;
  font-weight: 600;
  text-decoration: none;
}

.property-title-link:hover {
  text-decoration: underline;
}

.audit-note {
  color: #909399;
  font-size: 13px;
}
</style>
