<template>
  <div class="admin-users" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>账号与人员管理</h2>
        <p>前台用户和后台工作人员分开管理，避免账号角色混淆。</p>
      </div>
      <el-button @click="fetchUsers">刷新</el-button>
    </div>

    <el-row :gutter="12" class="summary-row">
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="前台用户" :value="frontUsers.length" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="后台人员" :value="staffUsers.length" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="超级管理员" :value="adminCount" />
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" type="border-card" class="account-tabs">
      <el-tab-pane label="前台用户" name="front">
        <div class="tab-toolbar">
          <span>只管理租客、房东等前台身份。</span>
          <el-input v-model="frontKeyword" placeholder="搜索用户名 / 邮箱 / 手机号" clearable />
        </div>

        <el-table :data="filteredFrontUsers" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" min-width="130" />
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="phone" label="手机号" min-width="130" />
          <el-table-column label="前台角色" width="140">
            <template #default="{ row }">
              <el-select
                :model-value="row.role"
                size="small"
                @change="(val: string) => handleRoleChange(row.id, val)"
              >
                <el-option label="租客" value="tenant" />
                <el-option label="房东" value="landlord" />
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
          <el-table-column label="注册时间" width="140">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="后台人员" name="staff">
        <div class="tab-toolbar">
          <span>只管理平台内部工作人员和超级管理员。</span>
          <el-input v-model="staffKeyword" placeholder="搜索工作人员账号 / 邮箱 / 手机号" clearable />
        </div>

        <el-table :data="filteredStaffUsers" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="账号" min-width="130" />
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="phone" label="手机号" min-width="130" />
          <el-table-column label="工作人员角色" width="170">
            <template #default="{ row }">
              <el-select
                :model-value="row.role"
                size="small"
                :disabled="row.role === 'admin'"
                @change="(val: string) => handleRoleChange(row.id, val)"
              >
                <el-option label="预约对接人员" value="appointment_staff" />
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
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminService } from '@/services/admin'
import { userService } from '@/services/user'
import type { User } from '@/types/user'

const users = ref<User[]>([])
const loading = ref(false)
const activeTab = ref('front')
const frontKeyword = ref('')
const staffKeyword = ref('')

const frontRoles = ['tenant', 'landlord']
const staffRoles = ['appointment_staff', 'property_manager', 'repair_worker', 'admin']

const frontUsers = computed(() => users.value.filter((user) => frontRoles.includes(user.role)))
const staffUsers = computed(() => users.value.filter((user) => staffRoles.includes(user.role)))
const adminCount = computed(() => users.value.filter((user) => user.role === 'admin').length)

const filteredFrontUsers = computed(() => filterUsers(frontUsers.value, frontKeyword.value))
const filteredStaffUsers = computed(() => filterUsers(staffUsers.value, staffKeyword.value))

function filterUsers(items: User[], keyword: string) {
  const value = keyword.trim().toLowerCase()
  if (!value) return items
  return items.filter((user) =>
    [user.username, user.email || '', user.phone || ''].some((text) => text.toLowerCase().includes(value)),
  )
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await userService.list()
  } finally {
    loading.value = false
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

onMounted(fetchUsers)
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
</style>
