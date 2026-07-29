<template>
  <div class="bookings-page" v-loading="loading">
    <div class="page-header">
    </div>

    <el-empty v-if="!loading && bookings.length === 0" description="暂无任何预订记录">
      <el-button type="primary" @click="$router.push('/search')">去找房</el-button>
    </el-empty>

    <div v-else class="booking-list">
      <div v-for="booking in bookings" :key="booking.id" class="booking-card">
        <div class="booking-left">
          <span class="booking-id">#{{ booking.id }}</span>
          <div class="booking-info">
            <p class="booking-prop" @click="$router.push(`/property/${booking.property_id}`)">
              房源 #{{ booking.property_id }}
            </p>
            <p v-if="booking.scheduled_date" class="booking-date">
              📅 {{ booking.scheduled_date }}
            </p>
            <p v-if="booking.message" class="booking-msg">
              💬 {{ booking.message }}
            </p>
            <div class="booking-progress">
              <div
                v-for="step in orderSteps(booking)"
                :key="step.key"
                class="order-step"
                :class="{ done: step.done, active: step.active }"
              >
                <i>{{ step.done ? '✓' : '' }}</i>
                <span>{{ step.label }}</span>
              </div>
            </div>
            <div class="booking-extra">
              <span v-if="booking.room_number">房间号：{{ booking.room_number }}</span>
              <span v-if="booking.lease_start || booking.lease_end">租期：{{ booking.lease_start || '待定' }} ~ {{ booking.lease_end || '待定' }}</span>
              <span>合同：{{ contractLabel(booking.contract_status) }}</span>
            </div>
          </div>
        </div>
        <div class="booking-right">
          <el-tag :type="statusTag(booking.status)" size="large" round>
            {{ statusLabel(booking.status) }}
          </el-tag>
          <div class="booking-actions">
            <el-button
              v-if="booking.status === 'pending'"
              type="danger" size="small" round
              @click="handleCancel(booking.id)"
            >
              取消预订
            </el-button>
            <el-button
              v-if="booking.contract_status === 'pending_signature' || booking.contract_status === 'signed'"
              type="primary" size="small" round
              @click="goConfirmRent(booking)"
            >
              {{ booking.contract_status === 'signed' ? '支付定金' : '查看合同' }}
            </el-button>
            <el-button
              v-if="booking.status === 'completed'"
              type="primary" size="small" round text
              @click="$router.push(`/property/${booking.property_id}`)"
            >
              查看房源
            </el-button>
          </div>
          <span class="booking-time">{{ formatDate(booking.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bookingService } from '@/services/booking'
import type { Booking } from '@/types/booking'

const router = useRouter()
const bookings = ref<Booking[]>([])
const loading = ref(false)

const statusLabels: Record<string, string> = {
  pending: '待确认', approved: '已确认', rejected: '已拒绝',
  cancelled: '已取消', completed: '已完成',
}
const statusTags: Record<string, string> = {
  pending: 'warning', approved: 'success', rejected: 'danger',
  cancelled: 'info', completed: '',
}
const fallbackSteps = [
  { key: 'submitted', label: '提交申请' },
  { key: 'profile_review', label: '资料审核' },
  { key: 'tenant_confirmed', label: '租客确认' },
  { key: 'landlord_confirmed', label: '管理员确认' },
  { key: 'contract_ready', label: '合同签署' },
  { key: 'deposit_paid', label: '支付定金' },
  { key: 'completed', label: '完成入住' },
]

function statusLabel(s: string) { return statusLabels[s] || s }
function statusTag(s: string) { return statusTags[s] || 'info' }
function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }
function contractLabel(status?: string | null) {
  return ({ not_ready: '待双方确认', pending_signature: '待签署', signed: '已签署' } as Record<string, string>)[status || 'not_ready'] || '待双方确认'
}
function orderSteps(booking: Booking) {
  if (booking.progress_steps?.length) return booking.progress_steps
  const activeMap: Record<string, string> = {
    pending: 'submitted',
    approved: 'landlord_confirmed',
    completed: 'completed',
    rejected: 'submitted',
    cancelled: 'submitted',
  }
  const activeKey = activeMap[booking.status] || 'submitted'
  const activeIndex = fallbackSteps.findIndex((step) => step.key === activeKey)
  return fallbackSteps.map((step, index) => ({
    ...step,
    done: index <= activeIndex,
    active: index === activeIndex,
  }))
}

async function fetchBookings() {
  loading.value = true
  try {
    bookings.value = await bookingService.list()
  }
  catch { /* ignore */ }
  finally { loading.value = false }
}

async function handleCancel(id: number) {
  try {
    await ElMessageBox.confirm('确定要取消此预约吗？', '确认取消', {
      confirmButtonText: '确定', cancelButtonText: '返回', type: 'warning',
    })
    await bookingService.cancel(id)
    ElMessage.success('预约已取消')
    fetchBookings()
  } catch { /* cancelled */ }
}

function goConfirmRent(booking: Booking) {
  router.push({ path: `/booking/payment/${booking.id}` })
}

onMounted(fetchBookings)
</script>

<style scoped>
.bookings-page {
  max-width: 860px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}

.booking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.booking-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.2s;
}

.booking-card:hover {
  box-shadow: var(--shadow);
  border-color: var(--primary);
}

.booking-left {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.booking-id {
  font-weight: 700;
  color: var(--primary);
  font-size: 13px;
  white-space: nowrap;
  margin-top: 2px;
}

.booking-prop {
  font-size: 15px;
  font-weight: 600;
  color: var(--primary);
  cursor: pointer;
  margin-bottom: 4px;
}

.booking-prop:hover { text-decoration: underline; }

.booking-date, .booking-msg {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.booking-progress {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.order-step {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-muted);
}

.order-step i {
  width: 18px;
  height: 18px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid var(--border);
  font-style: normal;
  font-size: 11px;
  background: #fff;
}

.order-step.done {
  color: var(--text-primary);
}

.order-step.done i {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.order-step.active {
  font-weight: 700;
}

.booking-extra {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.booking-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.booking-actions {
  display: flex;
  gap: 6px;
}

.booking-time {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
