<template>
  <div class="complaint-page">
    <section class="complaint-header">
      <div>
        <p>平台投诉与纠纷入口</p>
        <h1>提交投诉</h1>
      </div>
      <el-tag type="warning" effect="plain">提交后进入超级管理员仲裁中心</el-tag>
    </section>

    <section class="complaint-layout">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="complaint-form"
      >
        <div class="form-grid">
          <el-form-item label="投诉类型" prop="category">
            <el-select v-model="form.category" placeholder="请选择投诉类型">
              <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>

          <el-form-item label="所在城市" prop="city">
            <el-select v-model="form.city" placeholder="请选择城市" filterable allow-create>
              <el-option v-for="item in cities" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>

          <el-form-item label="投诉人姓名" prop="complainantName">
            <el-input v-model="form.complainantName" placeholder="请输入姓名" />
          </el-form-item>

          <el-form-item label="联系方式" prop="contact">
            <el-input v-model="form.contact" placeholder="手机号、邮箱或微信号" />
          </el-form-item>
        </div>

        <el-form-item label="关联房源" prop="property">
          <el-input v-model="form.property" placeholder="可填写房源名称、地址或预约单号" />
        </el-form-item>

        <el-form-item label="投诉标题" prop="title">
          <el-input v-model="form.title" maxlength="120" show-word-limit placeholder="用一句话说明问题" />
        </el-form-item>

        <el-form-item label="问题描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="7"
            maxlength="2000"
            show-word-limit
            placeholder="请写明时间、房源、对接人、诉求和已掌握的证明材料"
          />
        </el-form-item>

        <div class="form-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" :loading="submitting" @click="submitComplaint">提交投诉</el-button>
        </div>
      </el-form>

      <aside class="process-panel">
        <h2>处理流程</h2>
        <ol>
          <li>客户提交投诉信息</li>
          <li>系统同步到仲裁中心</li>
          <li>管理员指派核实或直接处理</li>
          <li>结案结果写入不可删除日志</li>
        </ol>

        <div v-if="submitted" class="result-box">
          <span>已提交</span>
          <strong>{{ submitted.id }}</strong>
          <p>当前状态：{{ submitted.status }}</p>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { adminPortalService, type ComplaintCreate } from '@/services/adminPortal'

const formRef = ref<FormInstance>()
const submitting = ref(false)
const categories = ref(['房源问题', '服务问题', '押金问题', '合同问题', '其他'])
const cities = ref(['伦敦', '纽约', '悉尼'])
const submitted = ref<{ id: string; status: string } | null>(null)

const form = reactive<ComplaintCreate>({
  category: '',
  title: '',
  description: '',
  complainantName: '',
  contact: '',
  city: '',
  property: '',
})

const rules: FormRules = {
  category: [{ required: true, message: '请选择投诉类型', trigger: 'change' }],
  city: [{ required: true, message: '请选择城市', trigger: 'change' }],
  complainantName: [{ required: true, message: '请输入投诉人姓名', trigger: 'blur' }],
  contact: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  title: [{ required: true, min: 2, message: '请输入至少 2 个字的标题', trigger: 'blur' }],
  description: [{ required: true, min: 5, message: '请补充更完整的问题描述', trigger: 'blur' }],
}

onMounted(async () => {
  try {
    const options = await adminPortalService.getPublicOptions()
    categories.value = options.categories
    cities.value = options.cities
  } catch {
    // Keep local defaults when the backend is not available.
  }
})

function resetForm() {
  formRef.value?.resetFields()
  form.property = ''
  submitted.value = null
}

async function submitComplaint() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const result = await adminPortalService.createComplaint({ ...form })
    submitted.value = { id: result.id, status: result.status }
    ElMessage.success(`投诉已提交：${result.id}`)
    formRef.value?.resetFields()
    form.property = ''
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.complaint-page {
  max-width: 1180px;
  margin: 0 auto;
}

.complaint-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 18px;
}

.complaint-header p {
  margin: 0 0 6px;
  color: var(--text-secondary);
  font-size: 14px;
}

.complaint-header h1 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
}

.complaint-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  align-items: start;
}

.complaint-form,
.process-panel {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.process-panel h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

.process-panel ol {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
  line-height: 1.9;
}

.result-box {
  margin-top: 18px;
  padding: 14px;
  border-radius: 8px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
}

.result-box span {
  color: #0369a1;
  font-size: 13px;
}

.result-box strong {
  display: block;
  margin-top: 4px;
  font-size: 22px;
  color: #0f172a;
}

.result-box p {
  margin: 6px 0 0;
  color: #475569;
}

@media (max-width: 900px) {
  .complaint-header,
  .form-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .complaint-layout,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
