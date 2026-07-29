<template>
  <div class="manage-page">
    <div class="page-header">
      <div>
        <h2>房源管理</h2>
        <p>按状态、区域、户型和价格范围归类管理，避免房源规模扩大后只剩一张散表。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refreshProperties">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="goCreate">发布新房源</el-button>
      </div>
    </div>

    <section class="summary-grid">
      <button
        v-for="item in summaryCards"
        :key="item.key"
        type="button"
        class="summary-card"
        :class="{ active: statusFilter === item.status }"
        @click="statusFilter = item.status"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </button>
    </section>

    <section class="manage-shell">
      <aside class="range-panel">
        <div class="panel-title">
          <span>管理范围</span>
          <el-tag size="small" type="info">{{ filteredProperties.length }} 套</el-tag>
        </div>

        <el-segmented v-model="statusFilter" :options="statusOptions" block />

        <div class="range-list">
          <button
            type="button"
            class="range-item"
            :class="{ active: districtFilter === '' }"
            @click="districtFilter = ''"
          >
            <span>全部区域</span>
            <strong>{{ properties.length }}</strong>
          </button>
          <button
            v-for="item in districtGroups"
            :key="item.district"
            type="button"
            class="range-item"
            :class="{ active: districtFilter === item.district }"
            @click="districtFilter = item.district"
          >
            <span>{{ item.district || '未填写区域' }}</span>
            <strong>{{ item.count }}</strong>
            <small>均价 {{ formatMoney(item.avgRent) }}</small>
          </button>
        </div>
      </aside>

      <main class="content-panel">
        <div class="filter-bar">
          <el-input
            v-model="keyword"
            class="keyword-input"
            :prefix-icon="Search"
            clearable
            placeholder="搜索标题、地址、区域"
          />
          <el-select v-model="typeFilter" clearable placeholder="房源类型" class="filter-select">
            <el-option
              v-for="(label, value) in typeLabels"
              :key="value"
              :label="label"
              :value="value"
            />
          </el-select>
          <el-select v-model="bedroomFilter" clearable placeholder="户型范围" class="filter-select">
            <el-option label="一居" value="1" />
            <el-option label="二居" value="2" />
            <el-option label="三居" value="3" />
            <el-option label="四居及以上" value="4+" />
          </el-select>
          <el-select v-model="sortKey" placeholder="排序" class="sort-select">
            <el-option label="最新发布" value="newest" />
            <el-option label="租金从高到低" value="price_desc" />
            <el-option label="租金从低到高" value="price_asc" />
            <el-option label="面积从大到小" value="area_desc" />
          </el-select>
        </div>

        <div class="scope-strip">
          <div>
            <span>当前范围</span>
            <strong>{{ currentScopeLabel }}</strong>
          </div>
          <div>
            <span>可租占比</span>
            <strong>{{ availableRate }}%</strong>
          </div>
          <div>
            <span>平均租金</span>
            <strong>{{ formatMoney(filteredAverageRent) }}</strong>
          </div>
          <div>
            <span>维护关注</span>
            <strong>{{ filteredMaintenanceCount }} 套</strong>
          </div>
        </div>

        <el-table :data="filteredProperties" v-loading="loading" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="房源信息" min-width="260">
            <template #default="{ row }">
              <div class="property-title">{{ row.title }}</div>
              <div class="property-meta">{{ row.address }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="district" label="区域" width="110" />
          <el-table-column label="月租" width="120" sortable>
            <template #default="{ row }">
              <span class="rent-text">{{ formatMoney(row.price_monthly) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="户型/面积" width="130">
            <template #default="{ row }">
              {{ row.bedrooms }}室{{ row.bathrooms }}卫
              <span v-if="row.area_sqm" class="area-text">· {{ row.area_sqm }}㎡</span>
            </template>
          </el-table-column>
          <el-table-column prop="property_type" label="类型" width="90">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ typeLabels[row.property_type as PropertyType] }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="150">
            <template #default="{ row }">
              <el-select
                :model-value="row.status"
                size="small"
                @change="(val: string) => updateStatus(row, val as PropertyStatus)"
              >
                <el-option label="可租" value="available" />
                <el-option label="已租" value="rented" />
                <el-option label="维护中" value="maintenance" />
                <el-option label="已下架" value="offline" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="editProperty(row.id)">编辑</el-button>
              <el-button size="small" text type="success" @click="manageImages(row.id)">图片</el-button>
              <el-popconfirm
                title="确定删除该房源吗？"
                confirm-button-text="删除"
                cancel-button-text="取消"
                @confirm="deleteProperty(row.id)"
              >
                <template #reference>
                  <el-button size="small" text type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </main>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import { usePropertyStore } from '@/stores/property'
import type { Property, PropertyStatus, PropertyType } from '@/types/property'

const router = useRouter()
const propertyStore = usePropertyStore()
const { properties, loading } = storeToRefs(propertyStore)

const keyword = ref('')
const statusFilter = ref<PropertyStatus | ''>('')
const districtFilter = ref('')
const typeFilter = ref<PropertyType | ''>('')
const bedroomFilter = ref('')
const sortKey = ref('newest')

const statusLabels: Record<PropertyStatus, string> = {
  available: '可租',
  rented: '已租',
  maintenance: '维护中',
  offline: '已下架',
}

const typeLabels: Record<PropertyType, string> = {
  apartment: '公寓',
  house: '别墅',
  studio: '单间',
  shared: '合租',
}

const statusOptions = computed(() => [
  { label: `全部 ${properties.value.length}`, value: '' },
  ...Object.entries(statusLabels).map(([value, label]) => ({
    label: `${label} ${countByStatus(value as PropertyStatus)}`,
    value,
  })),
])

const summaryCards = computed(() => [
  { key: 'all', label: '全部房源', value: properties.value.length, hint: '当前账号可管理范围', status: '' as const },
  { key: 'available', label: '可租', value: countByStatus('available'), hint: '可以继续推广', status: 'available' as const },
  { key: 'rented', label: '已租', value: countByStatus('rented'), hint: '进入合同与租期管理', status: 'rented' as const },
  { key: 'maintenance', label: '维护中', value: countByStatus('maintenance'), hint: '需要跟进维修状态', status: 'maintenance' as const },
  { key: 'offline', label: '已下架', value: countByStatus('offline'), hint: '暂不对外展示', status: 'offline' as const },
])

const districtGroups = computed(() => {
  const map = new Map<string, { district: string, count: number, totalRent: number }>()
  properties.value.forEach((property) => {
    const key = property.district || '未填写区域'
    const item = map.get(key) || { district: key, count: 0, totalRent: 0 }
    item.count += 1
    item.totalRent += Number(property.price_monthly || 0)
    map.set(key, item)
  })
  return Array.from(map.values())
    .map((item) => ({ ...item, avgRent: Math.round(item.totalRent / Math.max(item.count, 1)) }))
    .sort((a, b) => b.count - a.count)
})

const filteredProperties = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  const list = properties.value.filter((property) => {
    const matchesKeyword = !text || [property.title, property.address, property.district]
      .some((value) => String(value || '').toLowerCase().includes(text))
    const matchesStatus = !statusFilter.value || property.status === statusFilter.value
    const matchesDistrict = !districtFilter.value || property.district === districtFilter.value
    const matchesType = !typeFilter.value || property.property_type === typeFilter.value
    const matchesBedroom = !bedroomFilter.value || (
      bedroomFilter.value === '4+'
        ? property.bedrooms >= 4
        : property.bedrooms === Number(bedroomFilter.value)
    )
    return matchesKeyword && matchesStatus && matchesDistrict && matchesType && matchesBedroom
  })

  return [...list].sort((a, b) => {
    if (sortKey.value === 'price_desc') return b.price_monthly - a.price_monthly
    if (sortKey.value === 'price_asc') return a.price_monthly - b.price_monthly
    if (sortKey.value === 'area_desc') return Number(b.area_sqm || 0) - Number(a.area_sqm || 0)
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

const currentScopeLabel = computed(() => {
  const parts = [
    districtFilter.value || '全部区域',
    statusFilter.value ? statusLabels[statusFilter.value] : '全部状态',
    typeFilter.value ? typeLabels[typeFilter.value] : '',
  ].filter(Boolean)
  return parts.join(' / ')
})

const filteredAverageRent = computed(() => {
  if (!filteredProperties.value.length) return 0
  const total = filteredProperties.value.reduce((sum, item) => sum + Number(item.price_monthly || 0), 0)
  return Math.round(total / filteredProperties.value.length)
})

const filteredMaintenanceCount = computed(() =>
  filteredProperties.value.filter((item) => item.status === 'maintenance').length
)

const availableRate = computed(() => {
  if (!filteredProperties.value.length) return 0
  const available = filteredProperties.value.filter((item) => item.status === 'available').length
  return Math.round((available / filteredProperties.value.length) * 100)
})

function countByStatus(status: PropertyStatus) {
  return properties.value.filter((property) => property.status === status).length
}

function formatMoney(value: number | null | undefined) {
  return `¥${Number(value || 0).toLocaleString()}`
}

function goCreate() {
  router.push('/property/create')
}

function editProperty(id: number) {
  router.push('/property/' + id + '/edit')
}

function manageImages(id: number) {
  router.push('/property/' + id + '/images')
}

async function updateStatus(property: Property, newStatus: PropertyStatus) {
  if (property.status === newStatus) return
  try {
    await propertyStore.update(property.id, { status: newStatus })
    ElMessage.success(`房源状态已改为${statusLabels[newStatus]}`)
    refreshProperties()
  } catch {
    // handled by interceptor
  }
}

async function deleteProperty(id: number) {
  try {
    await propertyStore.remove(id)
    ElMessage.success('房源已删除')
  } catch {
    // handled by interceptor
  }
}

function refreshProperties() {
  propertyStore.fetchList({ limit: 100 })
}

onMounted(refreshProperties)
</script>

<style scoped>
.manage-page {
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #7a7f8c;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.summary-card {
  text-align: left;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  padding: 14px;
  cursor: pointer;
  transition: border-color .2s, box-shadow .2s;
}

.summary-card:hover,
.summary-card.active {
  border-color: #ee7040;
  box-shadow: 0 8px 22px rgba(238, 112, 64, .12);
}

.summary-card span,
.summary-card small {
  display: block;
  color: #858b96;
}

.summary-card strong {
  display: block;
  margin: 8px 0 4px;
  font-size: 24px;
  color: #303133;
}

.manage-shell {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.range-panel,
.content-panel {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.range-panel {
  padding: 14px;
  position: sticky;
  top: 92px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
}

.range-list {
  margin-top: 12px;
  display: grid;
  gap: 8px;
  max-height: 520px;
  overflow: auto;
}

.range-item {
  border: 1px solid #edf0f5;
  border-radius: 8px;
  background: #fafbfc;
  padding: 10px;
  text-align: left;
  cursor: pointer;
}

.range-item.active {
  border-color: #ee7040;
  background: #fff7f3;
}

.range-item span,
.range-item small {
  display: block;
  color: #7a7f8c;
}

.range-item strong {
  display: block;
  margin: 4px 0;
  color: #303133;
}

.content-panel {
  padding: 14px;
  min-width: 0;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.keyword-input {
  flex: 1 1 260px;
}

.filter-select {
  width: 140px;
}

.sort-select {
  width: 160px;
}

.scope-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.scope-strip div {
  border: 1px solid #edf0f5;
  border-radius: 8px;
  padding: 10px;
  background: #fafbfc;
}

.scope-strip span {
  display: block;
  margin-bottom: 4px;
  color: #8a9099;
  font-size: 12px;
}

.scope-strip strong {
  color: #303133;
}

.property-title {
  color: #303133;
  font-weight: 600;
  line-height: 1.4;
}

.property-meta,
.area-text {
  color: #8a9099;
  font-size: 12px;
}

.rent-text {
  color: #f56c6c;
  font-weight: 700;
}

@media (max-width: 960px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .manage-shell {
    grid-template-columns: 1fr;
  }

  .range-panel {
    position: static;
  }

  .scope-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
