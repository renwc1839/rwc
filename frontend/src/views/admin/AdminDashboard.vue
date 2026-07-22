<template>
  <div class="dashboard" v-loading="loading">
    <header class="dashboard-header">
      <div>
        <p class="eyebrow">Admin Overview</p>
        <h2>管理总览</h2>
        <span>这里保留后台管理需要的全局数据、账号权限、房源资产和审计入口；具体业务处理放在运营工作台。</span>
      </div>
      <el-button :icon="Refresh" type="primary" @click="fetchDashboard">刷新数据</el-button>
    </header>

    <section class="dashboard-grid main">
      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>账号与权限</span>
            <el-button :icon="User" text type="primary" @click="go('/admin/users')">管理账号</el-button>
          </div>
        </template>
        <div class="role-list">
          <button v-for="role in roleSummary" :key="role.key" type="button" class="role-item drill-item" @click="openRole(role.routeRole)">
            <div>
              <strong>{{ role.name }}</strong>
              <span>{{ role.desc }}</span>
            </div>
            <b>{{ role.count }}</b>
          </button>
        </div>
        <div class="status-strip">
          <button type="button" @click="go('/admin/users')">后台账号 {{ portalState?.accounts?.length || 0 }} 个</button>
          <button type="button" @click="go('/admin/users')">停用账号 {{ disabledAccountCount }} 个</button>
          <button type="button" @click="go('/workspace?tab=schedules')">排班冲突 {{ scheduleConflictCount }} 条</button>
        </div>
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>房源资产</span>
            <el-button :icon="House" text type="primary" @click="go('/admin/properties')">房源审核</el-button>
          </div>
        </template>
        <div class="asset-summary">
          <button type="button" class="asset-total drill-item" @click="go('/admin/properties')">
            <span>房源总数</span>
            <strong>{{ stats.total_properties }}</strong>
            <small>来自当前数据库房源</small>
          </button>
          <div class="asset-meta">
            <button type="button" @click="go('/workspace?tab=bookings')">预约记录 {{ stats.total_bookings }}</button>
            <button type="button" @click="go('/workspace?tab=bookings')">待审核预约 {{ stats.pending_bookings }}</button>
            <button type="button" @click="go('/admin/users')">用户总量 {{ stats.total_users }}</button>
          </div>
        </div>
        <div v-if="countryGroups.length" class="country-groups">
          <button v-for="group in countryGroups" :key="group.name" type="button" class="country-group drill-item" @click="openCountry(group.name)">
            <div class="country-head">
              <strong>{{ group.name }}</strong>
              <span>{{ group.total }} 套 · {{ group.items.length }} 个城市/区域</span>
            </div>
            <div class="city-tags">
              <span v-for="item in group.preview" :key="item.district" class="city-tag" @click.stop="openDistrict(item.district)">
                {{ item.district }}
                <b>{{ item.count }}</b>
              </span>
              <span v-if="group.restCount" class="city-more">+{{ group.restCount }} 个</span>
            </div>
          </button>
        </div>
      </el-card>
    </section>

    <section class="dashboard-grid lower">
      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>全局数据</span>
            <el-button :icon="Setting" text type="primary" @click="go('/workspace')">运营工作台</el-button>
          </div>
        </template>
        <div class="metric-grid">
          <button v-for="metric in metrics" :key="metric.label" type="button" class="metric-item drill-item" @click="go(metric.to)">
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}</strong>
            <small>{{ metric.hint }}</small>
          </button>
        </div>
      </el-card>

      <el-card shadow="never" class="panel-card">
        <template #header>
          <div class="card-header">
            <span>最近操作</span>
            <el-button :icon="Document" text type="primary" @click="go('/admin/logs')">审计日志</el-button>
          </div>
        </template>
        <div class="log-list">
          <button v-for="log in recentLogs" :key="`${log.time}-${log.target}`" type="button" class="log-item drill-item" @click="go('/admin/logs')">
            <strong>{{ log.type }}</strong>
            <span>{{ log.content }}</span>
            <small>{{ log.operator }} · {{ formatTime(log.time) }}</small>
          </button>
        </div>
        <el-empty v-if="!recentLogs.length" description="暂无操作记录" :image-size="70" />
      </el-card>
    </section>

    <section class="section-block">
      <div class="section-title">
        <h3>管理入口</h3>
        <span>只保留管理员常用入口；业务推进请进入运营工作台。</span>
      </div>
      <div class="shortcut-grid">
        <button v-for="shortcut in shortcuts" :key="shortcut.label" type="button" class="shortcut" @click="go(shortcut.to)">
          <span class="shortcut-icon">
            <component :is="shortcut.icon" />
          </span>
          <span>{{ shortcut.label }}</span>
          <small>{{ shortcut.desc }}</small>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Document, House, Refresh, Setting, Upload, User } from '@element-plus/icons-vue'
import { adminService } from '@/services/admin'
import { adminPortalService, type PortalState } from '@/services/adminPortal'
import type { AdminStats } from '@/types/admin'

const router = useRouter()
const loading = ref(false)
const stats = ref<AdminStats>({
  total_users: 0,
  total_properties: 0,
  total_bookings: 0,
  pending_bookings: 0,
  properties_by_district: [],
})
const portalState = ref<PortalState | null>(null)

const pendingWorkOrders = computed(() => portalState.value?.workOrders?.filter((item) => !['已完成', '已完结'].includes(item.status)) || [])
const disabledAccountCount = computed(() => portalState.value?.accounts?.filter((item) => item.status !== '启用').length || 0)
const scheduleConflictCount = computed(() => portalState.value?.schedules?.filter((item) => item.status === '冲突').length || 0)

const metrics = computed(() => [
  { label: '用户', value: stats.value.total_users, hint: '租客与后台账号总量', to: '/admin/users' },
  { label: '房源', value: stats.value.total_properties, hint: '当前可管理房源', to: '/admin/properties' },
  { label: '预约', value: stats.value.total_bookings, hint: '真实预约记录', to: '/workspace?tab=bookings' },
  { label: '工单', value: pendingWorkOrders.value.length, hint: '运营工作台内未完成事项', to: '/workspace?tab=repairs' },
])

const countryKeywords: Record<string, string[]> = {
  英国: ['伦敦', '曼彻斯特', '伯明翰', '利物浦', '爱丁堡', '格拉斯哥', '布里斯托', '利兹', '谢菲尔德', '诺丁汉', 'London', 'Manchester', 'Birmingham', 'Liverpool', 'Edinburgh'],
  美国: ['纽约', '洛杉矶', '波士顿', '芝加哥', '西雅图', '旧金山', '华盛顿', '曼哈顿', 'New York', 'Los Angeles', 'Boston', 'Chicago', 'Seattle', 'San Francisco'],
  澳大利亚: ['悉尼', '墨尔本', '布里斯班', '阿德莱德', '珀斯', '堪培拉', 'Sydney', 'Melbourne', 'Brisbane', 'Adelaide', 'Perth'],
  加拿大: ['多伦多', '温哥华', '蒙特利尔', '渥太华', '滑铁卢', 'Toronto', 'Vancouver', 'Montreal', 'Ottawa', 'Waterloo'],
  新加坡: ['新加坡', 'Singapore'],
  日本: ['东京', '大阪', '京都', 'Tokyo', 'Osaka', 'Kyoto'],
  韩国: ['首尔', '釜山', 'Seoul', 'Busan'],
}

function countryOfDistrict(district: string) {
  for (const [country, keywords] of Object.entries(countryKeywords)) {
    if (keywords.some((keyword) => district.includes(keyword))) return country
  }
  return '其他国家/地区'
}

const countryGroups = computed(() => {
  const districts = [...(stats.value.properties_by_district || [])].sort((a, b) => b.count - a.count)
  if (!districts.length) return []
  const grouped = districts.reduce<Record<string, typeof districts>>((result, item) => {
    const country = countryOfDistrict(item.district)
    result[country] = result[country] || []
    result[country].push(item)
    return result
  }, {})
  const preferredOrder = ['英国', '美国', '澳大利亚', '加拿大', '新加坡', '日本', '韩国', '其他国家/地区']
  return Object.entries(grouped)
    .map(([name, items]) => ({
      name,
      items: items.sort((a, b) => b.count - a.count),
      total: items.reduce((sum, item) => sum + item.count, 0),
      preview: items.slice(0, 6),
      restCount: Math.max(items.length - 6, 0),
    }))
    .sort((a, b) => {
      const ai = preferredOrder.indexOf(a.name)
      const bi = preferredOrder.indexOf(b.name)
      if (ai !== -1 || bi !== -1) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi)
      return b.total - a.total
    })
})

const roleSummary = computed(() => {
  const accounts = portalState.value?.accounts || []
  return [
    { key: 'super_admin', routeRole: 'admin', name: '超级管理员', desc: '全局权限和最终调度', count: accounts.filter((item) => item.roleKey === 'super_admin').length },
    { key: 'appointment_staff', routeRole: 'appointment_staff', name: '预约对接人员', desc: '预约、客户沟通、维修分配', count: accounts.filter((item) => item.roleKey === 'appointment_staff').length },
    { key: 'property_manager', routeRole: 'property_manager', name: '房源管理人员', desc: '发布房源与房源运营', count: accounts.filter((item) => item.roleKey === 'property_manager').length },
    { key: 'repair_worker', routeRole: 'repair_worker', name: '维修工', desc: '处理维修节点和凭证', count: accounts.filter((item) => item.roleKey === 'repair_worker').length },
  ]
})

const recentLogs = computed(() => (portalState.value?.logs || []).slice(0, 5))

const shortcuts = [
  { label: '用户管理', desc: '查看租客和后台人员', icon: User, to: '/admin/users' },
  { label: '房源审核', desc: '打开房源并审核状态', icon: House, to: '/admin/properties' },
  { label: '运营工作台', desc: '预约、维修、消息处理', icon: Setting, to: '/workspace' },
  { label: '数据导入', desc: '批量导入房源数据', icon: Upload, to: '/admin/import' },
  { label: '审计日志', desc: '查看后台操作留痕', icon: Document, to: '/admin/logs' },
]

function formatTime(value: string) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN')
}

function go(path: string) {
  router.push(path)
}

function openRole(role: string) {
  router.push({ path: '/admin/users', query: { role } })
}

function openCountry(country: string) {
  router.push({ path: '/admin/properties', query: { country } })
}

function openDistrict(district: string) {
  router.push({ path: '/admin/properties', query: { q: district } })
}

async function fetchDashboard() {
  loading.value = true
  try {
    const [statsData, stateData] = await Promise.all([
      adminService.getStats(),
      adminPortalService.getState(),
    ])
    stats.value = statsData
    portalState.value = stateData
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)
</script>

<style scoped>
.dashboard { max-width: 1240px; margin: 0 auto; display: grid; gap: 18px; }
.dashboard-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; padding: 4px 0 6px; }
.eyebrow { margin: 0 0 4px; color: #e86b3a; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.dashboard h2 { font-size: 24px; color: #262a30; margin: 0 0 6px; }
.dashboard-header span,
.section-title span { color: #7b818c; font-size: 13px; }
.section-block,
.panel-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; }
.section-block { padding: 18px; }
.section-title,
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.section-title { margin-bottom: 14px; }
.section-title h3,
.card-header span { margin: 0; color: #303133; font-size: 16px; font-weight: 700; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(420px, 0.95fr); gap: 18px; }
.dashboard-grid.main { align-items: stretch; }
.dashboard-grid.lower { grid-template-columns: minmax(0, 0.85fr) minmax(420px, 1.15fr); }
.panel-card :deep(.el-card__body) { padding: 16px; }
.role-list,
.log-list { display: grid; gap: 10px; }
.role-item,
.log-item { border: 1px solid #edf0f5; border-radius: 8px; padding: 10px; }
.drill-item { cursor: pointer; text-align: left; background: #fff; color: inherit; transition: border-color 0.16s, box-shadow 0.16s, transform 0.16s; }
.drill-item:hover { border-color: #e86b3a; box-shadow: 0 8px 22px rgba(232, 107, 58, 0.1); transform: translateY(-1px); }
.role-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.role-item div,
.log-item { min-width: 0; display: grid; gap: 4px; }
.role-item strong,
.log-item strong { color: #303133; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.role-item span,
.log-item span,
.log-item small { color: #7b818c; font-size: 12px; line-height: 1.45; }
.role-item b { font-size: 22px; color: #e86b3a; }
.status-strip { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.status-strip button { border: 1px solid #e5e7eb; border-radius: 999px; padding: 5px 9px; color: #606266; background: #fafafa; font-size: 12px; cursor: pointer; }
.status-strip button:hover,
.asset-meta button:hover,
.city-tag:hover { border-color: #e86b3a; color: #e86b3a; }
.asset-summary { display: grid; grid-template-columns: 140px 1fr; gap: 14px; margin-bottom: 14px; }
.asset-total { border: 1px solid #edf0f5; border-radius: 8px; padding: 12px; display: grid; gap: 4px; }
.asset-total span,
.asset-total small,
.asset-meta button { color: #7b818c; font-size: 12px; }
.asset-total strong { color: #262a30; font-size: 30px; }
.asset-meta { display: grid; gap: 8px; align-content: center; }
.asset-meta button { border: 0; border-bottom: 1px solid #edf0f5; padding: 0 0 7px; background: transparent; text-align: left; cursor: pointer; }
.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.metric-item { border: 1px solid #edf0f5; border-radius: 8px; padding: 12px; display: grid; gap: 4px; }
.metric-item span { color: #7b818c; font-size: 12px; }
.metric-item strong { color: #262a30; font-size: 24px; }
.metric-item small { color: #909399; font-size: 12px; }
.country-groups { display: grid; gap: 10px; }
.country-group { border: 1px solid #edf0f5; border-radius: 8px; padding: 10px; background: #fcfcfd; width: 100%; }
.country-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
.country-head strong { color: #303133; font-size: 13px; }
.country-head span { color: #909399; font-size: 12px; }
.city-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.city-tag,
.city-more { border: 1px solid #e5e7eb; border-radius: 999px; padding: 5px 8px; background: #fff; color: #606266; font-size: 12px; display: inline-flex; align-items: center; gap: 6px; }
.city-tag { cursor: pointer; }
.city-tag b { color: #e86b3a; font-size: 12px; }
.city-more { color: #909399; background: #f7f8fa; }
.shortcut-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.shortcut { border: 1px solid #e5e7eb; background: #fff; border-radius: 8px; padding: 12px; display: grid; gap: 6px; text-align: left; cursor: pointer; color: #303133; min-height: 94px; }
.shortcut:hover { border-color: #e86b3a; box-shadow: 0 8px 22px rgba(232, 107, 58, 0.12); }
.shortcut-icon { width: 28px; height: 28px; border: 1px solid #f1d5c8; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; background: #fff8f4; }
.shortcut-icon svg { width: 15px; height: 15px; color: #e86b3a; }
.shortcut span { font-weight: 700; }
.shortcut small { color: #7b818c; line-height: 1.45; }

@media (max-width: 960px) {
  .dashboard-header,
  .section-title,
  .card-header { align-items: flex-start; flex-direction: column; }
  .dashboard-grid,
  .dashboard-grid.lower,
  .metric-grid,
  .shortcut-grid,
  .asset-summary { grid-template-columns: 1fr; }
  .country-head { align-items: flex-start; flex-direction: column; }
}
</style>
