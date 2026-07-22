<template>
  <div class="booking-confirm-page">
    <!-- Header -->
    <div class="page-header">
      <el-button text :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <h2>租房申请</h2>
    </div>

    <el-row :gutter="24">
      <!-- Left: Booking Form -->
      <el-col :span="16">
        <el-card shadow="never" class="step-card">
          <template #header><span class="card-title">📋 房客信息与看房申请</span></template>

          <div class="prefill-info" v-if="prefillDate">
            <el-tag type="success" effect="plain" size="large" round>
              已选：{{ prefillDate }} {{ slotLabel }}
            </el-tag>
          </div>

          <el-form ref="formRef" :model="bookingForm" :rules="rules" label-width="100px" label-position="top">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="📅 看房日期" prop="scheduled_date">
                  <el-date-picker
                    v-model="bookingForm.scheduled_date"
                    type="date"
                    placeholder="选择日期"
                    value-format="YYYY-MM-DD"
                    :disabled-date="disabledDate"
                    style="width:100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="🕐 时间段" prop="time_slot">
                  <el-select v-model="bookingForm.time_slot" placeholder="选择时间段" style="width:100%">
                    <el-option label="🌅 上午 9:00-12:00" value="morning" />
                    <el-option label="☀️ 下午 14:00-17:00" value="afternoon" />
                    <el-option label="🌙 晚间 19:00-21:00" value="evening" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="👤 姓名" prop="tenant_name">
                  <el-input v-model="bookingForm.tenant_name" placeholder="请输入真实姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="📱 联系方式" prop="contact_phone">
                  <el-input v-model="bookingForm.contact_phone" placeholder="手机号 / WhatsApp / 微信" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="🌍 国籍 / 地区" prop="nationality">
                  <el-input v-model="bookingForm.nationality" placeholder="例如：中国 / 新加坡 / 马来西亚" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="🪪 护照号 / 证件号" prop="passport_no">
                  <el-input v-model="bookingForm.passport_no" placeholder="用于租房资料审核" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="🎓 学校" prop="school">
                  <el-input v-model="bookingForm.school" placeholder="例如：UCL / 港大 / NUS" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="📚 学历 / 阶段" prop="education">
                  <el-select v-model="bookingForm.education" placeholder="请选择" style="width:100%">
                    <el-option label="本科" value="本科" />
                    <el-option label="硕士" value="硕士" />
                    <el-option label="博士" value="博士" />
                    <el-option label="语言班 / 预科" value="语言班 / 预科" />
                    <el-option label="工作人士" value="工作人士" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="🚪 意向房间号">
                  <el-input v-model="bookingForm.room_number" placeholder="如 A-1208 / 待分配" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="租期开始">
                  <el-date-picker v-model="bookingForm.lease_start" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="租期结束">
                  <el-date-picker v-model="bookingForm.lease_end" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="💬 给房东留言（选填）">
              <el-input
                v-model="bookingForm.message"
                type="textarea"
                :rows="3"
                placeholder="可备注签证咨询、长短租需求、校车接送等"
              />
            </el-form-item>

            <div class="form-footer">
              <el-button @click="$router.back()">取消</el-button>
              <el-button type="primary" size="large" :loading="submitting" @click="submitBooking">
                提交租房申请
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <!-- Right: Property Summary -->
      <el-col :span="8">
        <el-card shadow="never" class="summary-card">
          <template #header><span class="card-title">🏠 房源信息</span></template>

          <div class="summary-property" v-if="propertyInfo">
            <div class="summary-img" v-if="primaryImage">
              <img :src="primaryImage" :alt="propertyInfo.title" />
            </div>
            <h3 class="summary-title">{{ propertyInfo.title }}</h3>
            <p class="summary-addr">{{ propertyInfo.address }}</p>
            <div class="summary-tags">
              <el-tag size="small">{{ propertyInfo.bedrooms }}室{{ propertyInfo.bathrooms }}卫</el-tag>
              <el-tag size="small" type="info">{{ propertyInfo.property_type }}</el-tag>
              <el-tag size="small">{{ propertyInfo.district }}</el-tag>
            </div>

            <el-divider />
            <div class="mini-fees">
              <div class="mini-row"><span>月租</span><span>¥{{ propertyInfo?.price_monthly || 0 }}</span></div>
              <div class="mini-row"><span>押金</span><span>¥{{ propertyInfo?.deposit_amount || propertyInfo?.price_monthly || 0 }}</span></div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { usePropertyStore } from '@/stores/property'
import { bookingService } from '@/services/booking'

const route = useRoute()
const router = useRouter()
const propertyStore = usePropertyStore()

const submitting = ref(false)
const formRef = ref<FormInstance>()

// Prefill from dialog
const prefillDate = (route.query.date as string) || ''
const prefillSlot = (route.query.slot as string) || ''
const propertyId = Number(route.query.property_id) || 0

const slotLabels: Record<string, string> = {
  morning: '上午 9:00-12:00',
  afternoon: '下午 14:00-17:00',
  evening: '晚间 19:00-21:00',
}
const slotLabel = computed(() => slotLabels[prefillSlot] || '')

// Property info
const propertyInfo = ref<any>(null)
const primaryImage = computed(() => {
  const imgs = propertyInfo.value?.images
  if (!imgs?.length) return null
  const p = imgs.find((i: any) => i.is_primary) || imgs[0]
  return `/api/v1/uploads/${p.filename}`
})

// Disable past dates
function disabledDate(date: Date): boolean {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

// Form
const bookingForm = reactive({
  scheduled_date: prefillDate,
  time_slot: prefillSlot,
  tenant_name: '',
  contact_phone: '',
  nationality: '',
  passport_no: '',
  school: '',
  education: '',
  room_number: '',
  lease_start: '',
  lease_end: '',
  message: '',
})

const rules: FormRules = {
  tenant_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  contact_phone: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  nationality: [{ required: true, message: '请输入国籍或地区', trigger: 'blur' }],
  passport_no: [{ required: true, message: '请输入护照号或证件号', trigger: 'blur' }],
  school: [{ required: true, message: '请输入学校', trigger: 'blur' }],
  education: [{ required: true, message: '请选择学历阶段', trigger: 'change' }],
}

async function submitBooking() {
  if (!formRef.value) return
  if (!propertyId || propertyId <= 0) {
    ElMessage.error('房源信息异常，请从房源详情页重新进入')
    return
  }
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const timeSlotLabel = slotLabels[bookingForm.time_slot] || ''
    const fullMessage = [
      timeSlotLabel ? `【看房时段：${timeSlotLabel}】` : '',
      bookingForm.message || '',
    ].filter(Boolean).join('\n')
    await bookingService.create({
      property_id: propertyId,
      message: fullMessage || undefined,
      scheduled_date: bookingForm.scheduled_date || undefined,
      tenant_profile: {
        name: bookingForm.tenant_name,
        contact: bookingForm.contact_phone,
        nationality: bookingForm.nationality,
        passport_no: bookingForm.passport_no,
        school: bookingForm.school,
        education: bookingForm.education,
      },
      room_number: bookingForm.room_number || undefined,
      lease_start: bookingForm.lease_start || undefined,
      lease_end: bookingForm.lease_end || undefined,
    })
    ElMessage.success('租房申请已提交，可在个人中心查看订单进度')
    // 跳转到个人中心预订列表
    setTimeout(() => router.push('/profile?tab=bookings'), 1500)
  } catch (err: any) {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail
    if (status === 409) {
      ElMessage.warning('您已对该房源发起过预约')
    } else if (status === 403) {
      ElMessage.error('仅租客身份可预约看房，请切换为租客账号')
    } else if (status === 401) {
      ElMessage.error('请先登录后再预约')
    } else if (status === 404) {
      ElMessage.error('房源不存在或已下架')
    } else if (detail && typeof detail === 'string') {
      ElMessage.error(detail)
    } else {
      ElMessage.error('预约提交失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (propertyId) {
    try {
      propertyInfo.value = await propertyStore.fetchById(propertyId)
    } catch {
      // handle
    }
  }
})
</script>

<style scoped>
.booking-confirm-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 22px;
  margin: 0;
}

/* ── Step Card ─────────────────────── */

.step-card {
  border-radius: var(--radius) !important;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}

.prefill-info {
  margin-bottom: 16px;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

/* ── Summary Card ──────────────────── */

.summary-card {
  border-radius: var(--radius) !important;
  position: sticky;
  top: 80px;
}

.summary-img {
  height: 160px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: 12px;
}

.summary-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.summary-addr {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.summary-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.mini-fees {
  font-size: 14px;
}

.mini-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  color: var(--text-secondary);
}

.mini-row.total {
  font-weight: 700;
  color: var(--text-primary);
}

.mini-total {
  font-size: 18px;
  color: var(--danger);
  font-weight: 700;
}
</style>
