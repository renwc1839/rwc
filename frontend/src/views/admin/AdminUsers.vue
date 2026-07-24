<template>
  <div class="admin-users" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>账号与人员管理</h2>
        <p>租客和后台工作人员分开管理，房源发布与运营统一归入房源管理人员。</p>
      </div>
      <el-button @click="fetchUsers">刷新</el-button>
    </div>

    <el-row :gutter="12" class="summary-row">
      <el-col :span="8">
        <el-card shadow="never"><el-statistic title="租客用户" :value="frontUsers.length" /></el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><el-statistic title="后台人员" :value="staffUsers.length" /></el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><el-statistic title="超级管理员" :value="adminCount" /></el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" type="border-card" class="account-tabs">
      <el-tab-pane label="租客用户" name="front">
        <div class="tab-toolbar">
          <span>只展示前台租客账号，敏感联系方式默认脱敏。</span>
          <el-input v-model="frontKeyword" placeholder="搜索用户名 / 邮箱 / 手机号" clearable />
        </div>

        <el-table :data="filteredFrontUsers" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" min-width="130" />
          <el-table-column label="邮箱" min-width="180">
            <template #default="{ row }">{{ maskEmail(row.email) || '-' }}</template>
          </el-table-column>
          <el-table-column label="手机号" min-width="130">
            <template #default="{ row }">{{ maskPhone(row.phone) || '-' }}</template>
          </el-table-column>
          <el-table-column label="角色" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ roleText(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '正常' : row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="注册时间" width="140">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openUserDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="后台人员" name="staff">
        <div class="tab-toolbar">
          <span>后台人员按真实职责分开：房东、房源管理人员、预约对接人员、维修工分别管理。</span>
          <div class="toolbar-actions">
            <el-select v-model="staffRoleFilter" placeholder="全部后台角色" clearable>
              <el-option label="全部后台角色" value="all" />
              <el-option label="预约对接人员" value="appointment_staff" />
              <el-option label="房东" value="landlord" />
              <el-option label="房源管理人员" value="property_manager" />
              <el-option label="维修工" value="repair_worker" />
              <el-option label="超级管理员" value="admin" />
            </el-select>
            <el-input v-model="staffKeyword" placeholder="搜索工作人员账号 / 邮箱 / 手机号" clearable />
          </div>
        </div>

        <el-table :data="filteredStaffUsers" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="账号" min-width="130" />
          <el-table-column label="邮箱" min-width="180">
            <template #default="{ row }">{{ maskEmail(row.email) || '-' }}</template>
          </el-table-column>
          <el-table-column label="手机号" min-width="130">
            <template #default="{ row }">{{ maskPhone(row.phone) || '-' }}</template>
          </el-table-column>
          <el-table-column label="后台角色" width="180">
            <template #default="{ row }">
              <el-select
                :model-value="editableRole(row.role)"
                size="small"
                :disabled="row.role === 'admin'"
                @change="(val: string) => handleRoleChange(row.id, val)"
              >
                <el-option label="预约对接人员" value="appointment_staff" />
                <el-option label="房东" value="landlord" />
                <el-option label="房源管理人员" value="property_manager" />
                <el-option label="维修工" value="repair_worker" />
                <el-option label="超级管理员" value="admin" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '正常' : row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="140">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openUserDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="detailVisible" size="720px" :title="detailTitle" destroy-on-close>
      <div v-if="detailLoading" class="drawer-loading">加载中...</div>
      <template v-else-if="activeDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">#{{ activeDetail.user.id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ activeDetail.user.username }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ activeDetail.user.role_label || roleText(activeDetail.user.role) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ activeDetail.user.status === 'active' ? '正常' : activeDetail.user.status }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ activeDetail.user.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ activeDetail.user.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(activeDetail.user.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(activeDetail.user.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <section class="detail-section" v-if="activeDetail.tenant_bookings.length">
          <h3>租客租房 / 申请记录</h3>
          <el-table :data="activeDetail.tenant_bookings" size="small" stripe>
            <el-table-column prop="property_title" label="房源" min-width="180" />
            <el-table-column prop="room_number" label="房间" width="100" />
            <el-table-column label="租期" width="180">
              <template #default="{ row }">{{ leaseText(row) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">{{ bookingStatusText(row.status) }}</template>
            </el-table-column>
            <el-table-column label="定金" width="100">
              <template #default="{ row }">{{ row.deposit_status || '-' }}</template>
            </el-table-column>
          </el-table>
        </section>

        <section class="detail-section" v-if="activeDetail.managed_properties.length">
          <h3>管理 / 发布房源</h3>
          <el-table :data="activeDetail.managed_properties" size="small" stripe>
            <el-table-column prop="title" label="房源" min-width="180" />
            <el-table-column prop="district" label="区域" width="100" />
            <el-table-column label="月租" width="100">
              <template #default="{ row }">¥{{ row.price_monthly }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">{{ propertyStatusText(row.status) }}</template>
            </el-table-column>
          </el-table>
        </section>

        <section class="detail-section" v-if="staffTaskRows.length">
          <h3>处理事务</h3>
          <el-table :data="staffTaskRows" size="small" stripe>
            <el-table-column prop="type" label="类型" width="110" />
            <el-table-column prop="title" label="事项" min-width="180" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="related" label="关联单号" width="120" />
          </el-table>
        </section>

        <el-empty
          v-if="!activeDetail.tenant_bookings.length && !activeDetail.managed_properties.length && !staffTaskRows.length"
          description="暂无关联业务记录"
        />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminService } from '@/services/admin'
import { userService } from '@/services/user'
import type { AdminUserDetail, User } from '@/types/user'

const route = useRoute()
const users = ref<User[]>([])
const loading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const activeDetail = ref<AdminUserDetail | null>(null)
const activeTab = ref('front')
const frontKeyword = ref('')
const staffKeyword = ref('')
const staffRoleFilter = ref('all')

const frontRoles = ['tenant']
const staffRoles = ['landlord', 'appointment_staff', 'property_manager', 'repair_worker', 'admin']

const frontUsers = computed(() => users.value.filter((user) => frontRoles.includes(user.role)))
const staffUsers = computed(() => users.value.filter((user) => staffRoles.includes(user.role)))
const adminCount = computed(() => users.value.filter((user) => user.role === 'admin').length)

const filteredFrontUsers = computed(() => filterUsers(frontUsers.value, frontKeyword.value))
const filteredStaffUsers = computed(() => filterUsers(
  staffUsers.value.filter((user) => roleFilterMatch(user.role, staffRoleFilter.value)),
  staffKeyword.value,
))
const detailTitle = computed(() => activeDetail.value ? `${activeDetail.value.user.username} 的账号详情` : '账号详情')

const staffTaskRows = computed(() => {
  if (!activeDetail.value) return []
  const appointments = activeDetail.value.appointments.map((item) => ({
    type: '预约',
    title: item.property || item.customer || item.id,
    status: item.status || '-',
    related: item.id || '-',
  }))
  const repairs = activeDetail.value.repairs.map((item) => ({
    type: '维修',
    title: item.desc || item.property || item.id,
    status: item.status || '-',
    related: item.id || '-',
  }))
  const workOrders = activeDetail.value.work_orders.map((item) => ({
    type: item.type || '工单',
    title: item.title || item.content || item.id,
    status: item.status || '-',
    related: item.related || item.id || '-',
  }))
  const messages = activeDetail.value.messages.map((item) => ({
    type: '消息',
    title: item.content || item.title || item.id,
    status: item.status || '-',
    related: item.related || item.id || '-',
  }))
  return [...appointments, ...repairs, ...workOrders, ...messages].slice(0, 30)
})

function filterUsers(items: User[], keyword: string) {
  const value = keyword.trim().toLowerCase()
  if (!value) return items
  return items.filter((user) =>
    [user.username, user.email || '', user.phone || ''].some((text) => text.toLowerCase().includes(value)),
  )
}

function roleFilterMatch(role: string, filter: string) {
  if (!filter || filter === 'all') return true
  return role === filter
}

function roleText(role: string) {
  return {
    tenant: '租客',
    landlord: '房东',
    appointment_staff: '预约对接人员',
    property_manager: '房源管理人员',
    repair_worker: '维修工',
    admin: '超级管理员',
  }[role] || role
}

function editableRole(role: string) {
  return role
}

function maskEmail(value: string | null) {
  if (!value || !value.includes('@')) return value
  const [name, domain] = value.split('@')
  return `${name.slice(0, Math.min(2, name.length))}***@${domain}`
}

function maskPhone(value: string | null) {
  if (!value) return value
  if (value.length <= 4) return '***'
  return `${value.slice(0, 3)}****${value.slice(-4)}`
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatDateTime(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function leaseText(row: Record<string, any>) {
  if (!row.lease_start && !row.lease_end) return '-'
  return `${row.lease_start || '待定'} 至 ${row.lease_end || '待定'}`
}

function bookingStatusText(status: string) {
  return { pending: '待处理', approved: '已同意', rejected: '已拒绝', cancelled: '已取消', completed: '已完成' }[status] || status
}

function propertyStatusText(status: string) {
  return { available: '空置', rented: '已出租', maintenance: '维护中', offline: '待上架' }[status] || status
}

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await userService.list({ limit: 100 })
  } finally {
    loading.value = false
  }
}

async function openUserDetail(user: User) {
  detailVisible.value = true
  detailLoading.value = true
  activeDetail.value = null
  try {
    activeDetail.value = await adminService.getUserDetail(user.id)
  } catch {
    ElMessage.error('获取用户详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function handleRoleChange(userId: number, role: string) {
  try {
    await adminService.updateUserRole(userId, role)
    ElMessage.success('角色已更新')
    await fetchUsers()
  } catch {
    ElMessage.error('更新失败')
  }
}

function applyRouteFilter() {
  const role = typeof route.query.role === 'string' ? route.query.role : ''
  if (!role) return
  if (role === 'tenant') {
    activeTab.value = 'front'
    return
  }
  activeTab.value = 'staff'
  staffRoleFilter.value = role
}

watch(() => route.query.role, applyRouteFilter)

onMounted(() => {
  applyRouteFilter()
  fetchUsers()
})
</script>

<style scoped>
.admin-users {
  max-width: 1120px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 22px;
  color: #303133;
  margin: 0 0 6px;
}

.page-header p {
  color: #909399;
  margin: 0;
}

.summary-row {
  margin-bottom: 16px;
}

.account-tabs {
  border-radius: var(--radius) !important;
}

.tab-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  color: #606266;
}

.tab-toolbar .el-input {
  width: 280px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-actions .el-select {
  width: 170px;
}

.drawer-loading {
  color: #909399;
  padding: 24px 0;
  text-align: center;
}

.detail-section {
  margin-top: 22px;
}

.detail-section h3 {
  color: #303133;
  font-size: 16px;
  margin: 0 0 12px;
}
</style>
