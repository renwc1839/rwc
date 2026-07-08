<template>
  <div class="admin-portal">
    <aside class="portal-sidebar">
      <div class="brand">
        <div class="brand-mark">A</div>
        <div>
          <h1>超级管理员管理端</h1>
          <p>Admin Portal</p>
        </div>
      </div>

      <el-menu :default-active="activeModule" class="module-menu" @select="selectModule">
        <el-menu-item v-for="module in modules" :key="module.key" :index="module.key">
          <el-icon><component :is="module.icon" /></el-icon>
          <span>{{ module.label }}</span>
          <el-badge v-if="module.badge" :value="module.badge" class="menu-badge" />
        </el-menu-item>
      </el-menu>

      <div class="security-panel">
        <span>安全会话</span>
        <strong>账号密码 + 二次验证</strong>
        <p>敏感操作统一写入不可删除日志</p>
      </div>
    </aside>

    <main class="portal-main">
      <header class="portal-header">
        <div>
          <p class="eyebrow">境外租房平台</p>
          <h2>{{ currentModule?.label }}</h2>
        </div>
        <div class="header-actions">
          <el-input v-model="globalKeyword" :prefix-icon="Search" placeholder="搜索订单、房源、投诉、人员" clearable />
          <el-button :icon="Refresh" :loading="loading" @click="loadPortalData">刷新</el-button>
          <el-button type="primary" @click="openFrontendComplaint">打开前台投诉入口</el-button>
        </div>
      </header>

      <section class="module-tabs">
        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane v-for="tab in currentTabs" :key="tab.key" :label="tab.label" :name="tab.key" />
        </el-tabs>
      </section>

      <section class="content-shell" v-loading="loading">
        <template v-if="activeModule === 'dispatch'">
          <div v-if="activeTab === 'booking-dispatch'" class="panel">
            <PanelTitle title="预约调度" desc="查看预约订单，并执行分配、改期、取消、优先级标记。" />
            <div class="toolbar-actions">
              <el-select v-model="filters.city" placeholder="城市" clearable>
                <el-option v-for="city in cities" :key="city" :label="city" :value="city" />
              </el-select>
              <el-button type="primary" :icon="UserFilled" @click="bulkAssign">批量分配</el-button>
            </div>
            <el-table :data="filteredAppointments" border stripe>
              <el-table-column prop="id" label="编号" width="110" sortable />
              <el-table-column prop="customer" label="客户姓名" width="110" />
              <el-table-column prop="phone" label="联系方式" width="130" />
              <el-table-column prop="property" label="意向房源" min-width="190" />
              <el-table-column prop="time" label="预约时间" min-width="150" sortable />
              <el-table-column prop="city" label="城市" width="90" />
              <el-table-column prop="assignee" label="对接人" width="100" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="220">
                <template #default="{ row }">
                  <el-button size="small" @click="assignAppointment(row)">分配</el-button>
                  <el-button size="small" type="warning" @click="recordAction(row.id, '已标记优先级')">优先级</el-button>
                  <el-button size="small" type="danger" @click="recordAction(row.id, '已取消预约')">取消</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else-if="activeTab === 'property-dispatch'" class="panel">
            <PanelTitle title="房源调度" desc="管理房源可租、锁定、签约、下架状态，并处理冲突。" />
            <div class="status-grid">
              <div v-for="item in propertyStatusCards" :key="item.label" class="stat-card">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <el-table :data="properties" border stripe>
              <el-table-column prop="title" label="房源" min-width="200" />
              <el-table-column prop="city" label="城市" width="90" />
              <el-table-column prop="landlord" label="房东" width="120" />
              <el-table-column prop="lockedUntil" label="锁定到期" min-width="140" />
              <el-table-column prop="conflicts" label="冲突" width="80" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="230">
                <template #default="{ row }">
                  <el-button size="small" @click="updateItem('properties', row.id, '已预约')">锁定</el-button>
                  <el-button size="small" @click="updateItem('properties', row.id, '可租')">解锁</el-button>
                  <el-button size="small" type="danger" @click="updateItem('properties', row.id, '已下架')">下架</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else-if="activeTab === 'staff-dispatch'" class="panel">
            <PanelTitle title="人员调度" desc="查看人员排班、在岗状态、当前负载和跨城支援。" />
            <el-table :data="staff" border stripe>
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="city" label="负责城市" width="110" />
              <el-table-column prop="workTime" label="排班" width="140" />
              <el-table-column label="负载" min-width="160">
                <template #default="{ row }"><el-progress :percentage="row.load" :status="row.load >= 80 ? 'exception' : undefined" /></template>
              </el-table-column>
              <el-table-column prop="pending" label="待处理" width="90" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }"><el-tag :type="row.online ? 'success' : 'info'">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="220">
                <template #default="{ row }">
                  <el-button size="small" @click="updateItem('staff', row.id, '在岗')">设为在岗</el-button>
                  <el-button size="small" @click="updateItem('staff', row.id, '跨城支援')">跨城支援</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else class="panel">
            <PanelTitle title="异常督办" desc="集中处理超时未确认、带看后未反馈、签约超时和投诉未处理。" />
            <el-table :data="exceptions" border stripe>
              <el-table-column prop="type" label="异常类型" min-width="150" />
              <el-table-column prop="target" label="关联对象" min-width="160" />
              <el-table-column prop="owner" label="负责人" width="100" />
              <el-table-column prop="elapsed" label="超时" width="100" />
              <el-table-column label="级别" width="90">
                <template #default="{ row }"><el-tag :type="warningType(row.level)">{{ row.level }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="220">
                <template #default="{ row }">
                  <el-button size="small" @click="recordAction(row.id, `已催办 ${row.owner}`)">催办</el-button>
                  <el-button size="small" @click="updateItem('exceptions', row.id, '已转派')">转派</el-button>
                  <el-button size="small" type="warning" @click="updateItem('exceptions', row.id, '管理员介入')">介入</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'arbitration'">
          <div class="panel">
            <PanelTitle :title="selectedTab?.label || ''" :desc="selectedTab?.desc || ''" />
            <el-table :data="caseRows" border stripe>
              <el-table-column prop="caseNo" label="编号" width="110" sortable />
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="parties" label="双方/对象" min-width="160" />
              <el-table-column prop="amount" label="金额/影响" width="130" />
              <el-table-column prop="evidence" label="材料摘要" min-width="210" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="250">
                <template #default="{ row }">
                  <el-button size="small" @click="showEvidence(row)">查看</el-button>
                  <el-button size="small" type="primary" @click="openDecisionDialog(row)">处理</el-button>
                  <el-button size="small" type="danger" @click="rejectCase(row)">驳回</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'dashboard'">
          <div v-if="activeTab === 'realtime-dashboard'" class="panel">
            <div class="metric-grid">
              <div v-for="metric in metrics" :key="metric.label" class="metric-card">
                <span>{{ metric.label }}</span>
                <strong :class="{ danger: metric.danger }">{{ metric.value }}</strong>
                <p>{{ metric.hint }}</p>
              </div>
            </div>
            <div class="dashboard-grid">
              <div class="panel-block">
                <h3>各城市业务量 Top 5</h3>
                <div v-for="city in cityRankRows" :key="city.city" class="rank-row">
                  <span>{{ city.city }}</span>
                  <el-progress :percentage="city.percent" :stroke-width="12" />
                  <strong>{{ city.count }}</strong>
                </div>
              </div>
              <div class="panel-block">
                <h3>近 7 天预约 / 签约趋势</h3>
                <div class="trend-chart">
                  <div v-for="day in trendRows" :key="day.day" class="trend-bar">
                    <i :style="{ height: `${day.booking}px` }" />
                    <b :style="{ height: `${day.sign}px` }" />
                    <span>{{ day.day }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'business-analysis'" class="panel">
            <PanelTitle title="业务分析" desc="按城市、时间、房源和转化漏斗分析整体经营情况。" />
            <el-table :data="businessRows" border stripe>
              <el-table-column prop="city" label="城市" />
              <el-table-column prop="properties" label="房源量" />
              <el-table-column prop="bookings" label="预约量" />
              <el-table-column prop="contracts" label="签约量" />
              <el-table-column prop="conversion" label="转化率" />
            </el-table>
            <div class="funnel">
              <div v-for="step in funnelRows" :key="step.label" :style="{ width: `${step.width}%` }">{{ step.label }} {{ step.value }}</div>
            </div>
          </div>

          <div v-else-if="activeTab === 'staff-performance'" class="panel">
            <PanelTitle title="人员绩效" desc="查看每位对接人的带看、签约、响应和投诉表现。" />
            <el-table :data="performanceRows" border stripe>
              <el-table-column prop="name" label="人员" />
              <el-table-column prop="city" label="城市" />
              <el-table-column prop="visits" label="带看次数" />
              <el-table-column prop="contracts" label="签约数" />
              <el-table-column prop="rate" label="签约率" />
              <el-table-column prop="response" label="平均响应" />
              <el-table-column prop="complaints" label="投诉次数" />
              <el-table-column prop="score" label="满意度" />
            </el-table>
          </div>

          <div v-else class="panel">
            <PanelTitle title="预警中心" desc="业务、人员和房源异常预警集中处理。" />
            <el-table :data="warnings" border stripe>
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="content" label="预警内容" min-width="260" />
              <el-table-column label="级别" width="90">
                <template #default="{ row }"><el-tag :type="warningType(row.level)">{{ row.level }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="created" label="触发时间" min-width="150" />
              <el-table-column label="操作" width="150">
                <template #default="{ row }"><el-button size="small" @click="updateItem('warnings', row.id, '已处理')">标记已处理</el-button></template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'rules'">
          <div class="panel">
            <div class="panel-toolbar">
              <div>
                <h3>{{ selectedTab?.label }}</h3>
                <p>{{ selectedTab?.desc }}</p>
              </div>
              <el-button type="primary" @click="activeTab === 'penalty-rules' ? requestPenaltyRuleChange() : publishRules()">
                {{ activeTab === 'penalty-rules' ? '发起变更申请' : '发布规则' }}
              </el-button>
            </div>

            <el-form label-width="160px" class="rules-form">
              <template v-if="activeTab === 'booking-rules'">
                <el-form-item label="最少提前预约时间"><el-input-number v-model="rulesState.booking.advanceHours" :min="1" /> 小时</el-form-item>
                <el-form-item label="同时预约上限"><el-input-number v-model="rulesState.booking.maxActive" :min="1" /> 套</el-form-item>
                <el-form-item label="房源锁定时长"><el-input-number v-model="rulesState.booking.lockHours" :min="1" /> 小时</el-form-item>
                <el-form-item label="取消预约扣费"><el-switch v-model="rulesState.booking.cancelFee" /></el-form-item>
              </template>

              <template v-else-if="activeTab === 'deposit-rules'">
                <el-form-item label="押金比例"><el-select v-model="rulesState.deposit.ratio"><el-option label="押一付一" value="押一付一" /><el-option label="押二付一" value="押二付一" /></el-select></el-form-item>
                <el-form-item label="退款到账时间"><el-input-number v-model="rulesState.deposit.refundDays" :min="1" /> 个工作日</el-form-item>
                <el-form-item label="可扣款项目"><el-select v-model="rulesState.deposit.deductions" multiple filterable allow-create><el-option label="清洁费" value="清洁费" /><el-option label="维修费" value="维修费" /><el-option label="违约金" value="违约金" /></el-select></el-form-item>
              </template>

              <template v-else-if="activeTab === 'ai-rules'">
                <el-form-item v-for="item in aiWeightRows" :key="item.key" :label="item.label">
                  <el-slider v-model="rulesState.ai[item.key]" :min="0" :max="100" />
                </el-form-item>
                <el-form-item label="推荐结果数量"><el-input-number v-model="rulesState.ai.resultCount" :min="1" /></el-form-item>
              </template>

              <template v-else-if="activeTab === 'penalty-rules'">
                <div class="policy-grid">
                  <div class="policy-card">
                    <span>客户放鸽子处罚</span>
                    <strong>平台治理基线</strong>
                    <p>{{ rulesState.penalty.tenantNoShow }}</p>
                  </div>
                  <div class="policy-card">
                    <span>房东虚假房源处罚</span>
                    <strong>平台治理基线</strong>
                    <p>{{ rulesState.penalty.fakeProperty }}</p>
                  </div>
                  <div class="policy-card">
                    <span>投诉预警触发</span>
                    <strong>{{ rulesState.penalty.complaintLimit }} 次</strong>
                    <p>只作为系统预警阈值展示，不在此页直接调整。</p>
                  </div>
                </div>
                <div class="policy-lock">
                  <el-tag type="danger" effect="dark">底层逻辑锁定</el-tag>
                  <p>处罚规则会影响扣费、封号、下架和合作终止，不能由运营人员在页面中直接修改。需要先提交变更理由，再进入规则评审和版本发布流程。</p>
                </div>
              </template>

              <template v-else>
                <el-form-item label="通知场景"><el-input v-model="rulesState.notification.scene" /></el-form-item>
                <el-form-item label="通知方式"><el-select v-model="rulesState.notification.channels" multiple><el-option label="短信" value="短信" /><el-option label="邮件" value="邮件" /><el-option label="站内信" value="站内信" /><el-option label="微信通知" value="微信通知" /></el-select></el-form-item>
                <el-form-item label="通知对象"><el-select v-model="rulesState.notification.targets" multiple><el-option label="客户" value="客户" /><el-option label="房东" value="房东" /><el-option label="对接人" value="对接人" /><el-option label="管理员" value="管理员" /></el-select></el-form-item>
                <el-form-item label="模板内容"><el-input v-model="rulesState.notification.template" type="textarea" :rows="4" /></el-form-item>
              </template>
            </el-form>
          </div>
        </template>

        <template v-else>
          <div v-if="activeTab === 'accounts-permissions'" class="panel">
            <PanelTitle title="账号权限" desc="管理后台子账号、角色和启停状态。" />
            <el-table :data="accounts" border stripe>
              <el-table-column prop="name" label="账号" />
              <el-table-column prop="role" label="角色" />
              <el-table-column prop="phone" label="手机号" />
              <el-table-column label="二次验证"><template #default="{ row }"><el-tag :type="row.twoFactor ? 'success' : 'warning'">{{ row.twoFactor ? '已启用' : '未启用' }}</el-tag></template></el-table-column>
              <el-table-column label="状态"><template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template></el-table-column>
              <el-table-column label="操作" width="180">
                <template #default="{ row }">
                  <el-button size="small" @click="updateItem('accounts', row.id, row.status === '启用' ? '禁用' : '启用')">{{ row.status === '启用' ? '禁用' : '启用' }}</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else-if="activeTab === 'operation-logs'" class="panel">
            <PanelTitle title="操作日志" desc="所有后台操作完整记录，只可查看不可删除。" />
            <el-table :data="logs" border stripe>
              <el-table-column prop="operator" label="操作人" width="110" />
              <el-table-column prop="time" label="操作时间" min-width="170" />
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="target" label="对象" width="130" />
              <el-table-column prop="content" label="内容" min-width="260" />
              <el-table-column prop="ip" label="IP 地址" width="120" />
            </el-table>
          </div>

          <div v-else class="panel">
            <PanelTitle title="基础设置" desc="配置平台名称、客服联系方式、开通城市和第三方服务入口。" />
            <el-form label-width="130px" class="rules-form">
              <el-form-item label="平台名称"><el-input v-model="settings.platformName" /></el-form-item>
              <el-form-item label="客服电话"><el-input v-model="settings.servicePhone" /></el-form-item>
              <el-form-item label="开通城市"><el-select v-model="settings.cities" multiple filterable allow-create><el-option v-for="city in cities" :key="city" :label="city" :value="city" /></el-select></el-form-item>
              <el-form-item><el-button type="primary" @click="recordAction('settings', '基础设置已保存')">保存设置</el-button></el-form-item>
            </el-form>
          </div>
        </template>
      </section>
    </main>

    <el-dialog v-model="decisionDialogVisible" title="处理记录" width="520px">
      <el-form label-position="top">
        <el-form-item label="处理对象">
          <el-input :model-value="activeCase?.caseNo || ''" disabled />
        </el-form-item>
        <el-form-item label="处理结果">
          <el-select v-model="decisionForm.status">
            <el-option label="处理中" value="处理中" />
            <el-option label="已完结" value="已完结" />
            <el-option label="已仲裁" value="已仲裁" />
            <el-option label="已驳回" value="已驳回" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input v-model="decisionForm.result" type="textarea" :rows="4" placeholder="填写处理依据、赔偿/处罚/驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="decisionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDecision">提交并留痕</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  DataAnalysis,
  Finished,
  Operation,
  Refresh,
  Search,
  Tickets,
  UserFilled,
} from '@element-plus/icons-vue'
import { adminPortalService, type PortalState } from '@/services/adminPortal'

const PanelTitle = defineComponent({
  props: {
    title: { type: String, required: true },
    desc: { type: String, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'panel-toolbar' }, [h('div', [h('h3', props.title), h('p', props.desc)])])
  },
})

const router = useRouter()
const loading = ref(false)
const activeModule = ref('dashboard')
const activeTab = ref('realtime-dashboard')
const globalKeyword = ref('')
const filters = reactive({ city: '' })
const decisionDialogVisible = ref(false)
const activeCase = ref<any | null>(null)
const decisionForm = reactive({ status: '处理中', result: '' })

const modules = [
  {
    key: 'dispatch',
    label: '调度中心',
    icon: Operation,
    badge: 12,
    tabs: [
      { key: 'booking-dispatch', label: '预约调度', desc: '查看所有预约单，进行分配、改期、取消等调度操作。' },
      { key: 'property-dispatch', label: '房源调度', desc: '管理房源可租、锁定、签约、下架状态。' },
      { key: 'staff-dispatch', label: '人员调度', desc: '管理当地对接人员排班与负载。' },
      { key: 'exception-supervision', label: '异常督办', desc: '自动识别异常订单并集中督办。' },
    ],
  },
  {
    key: 'arbitration',
    label: '仲裁中心',
    icon: Finished,
    badge: 7,
    tabs: [
      { key: 'deposit-disputes', label: '押金纠纷', desc: '处理押金退款、扣款相关纠纷。' },
      { key: 'complaints', label: '投诉处理', desc: '处理客户和房东的各类投诉。' },
      { key: 'penalties', label: '违规处罚', desc: '对违规客户、房东、内部人员进行处罚。' },
      { key: 'special-approvals', label: '特例审批', desc: '处理特殊退款、破例预约、费用减免申请。' },
    ],
  },
  {
    key: 'dashboard',
    label: '数据看板',
    icon: DataAnalysis,
    tabs: [
      { key: 'realtime-dashboard', label: '实时大盘', desc: '今日核心数据一览。' },
      { key: 'business-analysis', label: '业务分析', desc: '多维度业务数据分析。' },
      { key: 'staff-performance', label: '人员绩效', desc: '各对接人员绩效数据。' },
      { key: 'warning-center', label: '预警中心', desc: '异常数据自动预警。' },
    ],
  },
  {
    key: 'system',
    label: '系统管理',
    icon: Tickets,
    tabs: [
      { key: 'accounts-permissions', label: '账号权限', desc: '管理子账号、角色和权限。' },
      { key: 'operation-logs', label: '操作日志', desc: '审计后台所有操作。' },
      { key: 'base-settings', label: '基础设置', desc: '配置平台基础信息。' },
    ],
  },
]

const appointments = ref<any[]>([])
const properties = ref<any[]>([])
const staff = ref<any[]>([])
const exceptions = ref<any[]>([])
const complaints = ref<any[]>([])
const arbitrations = ref<any[]>([])
const warnings = ref<any[]>([])
const accounts = ref<any[]>([])
const logs = ref<any[]>([])
const metrics = ref<any[]>([])
const cityRankRows = ref<any[]>([])
const trendRows = ref<any[]>([])
const settings = reactive<any>({ platformName: '', servicePhone: '', cities: [] })
const rulesState = reactive<any>({
  booking: { advanceHours: 4, maxActive: 3, lockHours: 24, cancelFee: true },
  deposit: { ratio: '押一付一', refundDays: 3, deductions: ['清洁费', '维修费'] },
  ai: { price: 80, distance: 70, room: 65, area: 55, facility: 60, score: 75, resultCount: 10, coldStart: 'hot-city' },
  penalty: { tenantNoShow: '', fakeProperty: '', complaintLimit: 3, levels: ['一般', '较重', '严重'] },
  notification: { scene: 'new-booking', channels: ['短信', '站内信'], targets: ['客户', '对接人'], template: '' },
})

const currentModule = computed(() => modules.find((item) => item.key === activeModule.value))
const currentTabs = computed(() => currentModule.value?.tabs || [])
const selectedTab = computed(() => currentTabs.value.find((item) => item.key === activeTab.value))
const cities = computed(() => Array.from(new Set([...settings.cities, ...properties.value.map((item) => item.city)].filter(Boolean))))
const filteredAppointments = computed(() => appointments.value.filter((item) => !filters.city || item.city === filters.city))
const propertyStatusCards = computed(() => ['可租', '已预约', '已签约', '已下架'].map((label) => ({ label, value: properties.value.filter((item) => item.status === label).length })))
const caseRows = computed(() => {
  if (activeTab.value === 'complaints') {
    return complaints.value.map((item) => ({
      caseNo: item.id,
      type: item.category,
      parties: `${item.complainantName} / ${item.property || '平台'}`,
      amount: item.city,
      evidence: item.title,
      status: item.status,
      result: item.result,
      source: 'complaint',
    }))
  }
  return arbitrations.value.map((item) => ({ ...item, source: 'arbitration' }))
})

const businessRows = [
  { city: '伦敦', properties: 286, bookings: 86, contracts: 21, conversion: '24.4%' },
  { city: '纽约', properties: 213, bookings: 73, contracts: 18, conversion: '24.7%' },
  { city: '悉尼', properties: 176, bookings: 55, contracts: 11, conversion: '20.0%' },
]
const funnelRows = [
  { label: '浏览', value: 12860, width: 100 },
  { label: '预约', value: 1420, width: 72 },
  { label: '带看', value: 638, width: 48 },
  { label: '签约', value: 186, width: 28 },
]
const performanceRows = [
  { name: 'Anna', city: '伦敦', visits: 42, contracts: 12, rate: '28.6%', response: '12 分钟', complaints: 1, score: 4.8 },
  { name: 'Mike', city: '纽约', visits: 35, contracts: 9, rate: '25.7%', response: '18 分钟', complaints: 2, score: 4.5 },
  { name: 'Sofia', city: '悉尼', visits: 28, contracts: 7, rate: '25.0%', response: '16 分钟', complaints: 0, score: 4.9 },
]
const aiWeightRows = [
  { key: 'price', label: '价格权重' },
  { key: 'distance', label: '距离权重' },
  { key: 'room', label: '房型权重' },
  { key: 'area', label: '面积权重' },
  { key: 'facility', label: '配套权重' },
  { key: 'score', label: '评分权重' },
]

onMounted(loadPortalData)

function selectModule(key: string) {
  activeModule.value = key
  activeTab.value = modules.find((item) => item.key === key)?.tabs[0]?.key || ''
}

function applyState(state: PortalState) {
  appointments.value = state.appointments || []
  properties.value = state.properties || []
  staff.value = state.staff || []
  exceptions.value = state.exceptions || []
  complaints.value = state.complaints || []
  arbitrations.value = state.arbitrations || []
  warnings.value = state.warnings || []
  accounts.value = state.accounts || []
  logs.value = state.logs || []
  Object.assign(settings, state.settings || {})
  Object.assign(rulesState, state.rules || {})
}

async function loadPortalData() {
  loading.value = true
  try {
    const [state, overview] = await Promise.all([adminPortalService.getState(), adminPortalService.getOverview()])
    applyState(state)
    metrics.value = overview.metrics
    cityRankRows.value = overview.cityRanks
    trendRows.value = overview.trend
  } finally {
    loading.value = false
  }
}

function statusType(status: string) {
  if (['已确认', '可租', '已签约', '已通过', '启用', '已完结', '已处理', '已仲裁'].includes(status)) return 'success'
  if (['待分配', '待确认', '待仲裁', '待处理'].includes(status)) return 'warning'
  if (['处理中', '已预约', '管理员介入', '跨城支援'].includes(status)) return 'primary'
  if (['已取消', '已驳回', '已下架', '禁用'].includes(status)) return 'danger'
  return 'info'
}

function warningType(level: string) {
  if (level === '紧急') return 'danger'
  if (level === '重要') return 'warning'
  return 'info'
}

async function assignAppointment(row: any) {
  const { value } = await ElMessageBox.prompt('请输入对接人姓名', `分配 ${row.id}`, {
    confirmButtonText: '确认分配',
    cancelButtonText: '取消',
  })
  await adminPortalService.assignAppointment(row.id, value)
  ElMessage.success('预约已分配')
  await loadPortalData()
}

async function bulkAssign() {
  if (!appointments.value.length) return
  await assignAppointment(appointments.value[0])
}

async function updateItem(collection: string, id: string, status: string) {
  await adminPortalService.updateItem(collection, id, { status })
  ElMessage.success('状态已更新并写入日志')
  await loadPortalData()
}

async function recordAction(target: string, message: string) {
  ElMessage.success(`${target}：${message}`)
}

function showEvidence(row: any) {
  ElMessageBox.alert(row.evidence || '暂无材料', `${row.caseNo} 材料摘要`)
}

function openDecisionDialog(row: any) {
  activeCase.value = row
  decisionForm.status = row.status === '待处理' ? '处理中' : row.status
  decisionForm.result = row.result || ''
  decisionDialogVisible.value = true
}

async function rejectCase(row: any) {
  activeCase.value = row
  decisionForm.status = '已驳回'
  decisionForm.result = '材料不足或不符合平台处理规则。'
  await submitDecision()
}

async function submitDecision() {
  if (!activeCase.value) return
  if (!decisionForm.result.trim()) {
    ElMessage.error('请填写处理说明')
    return
  }
  if (activeCase.value.source === 'complaint') {
    await adminPortalService.updateComplaint(activeCase.value.caseNo, { status: decisionForm.status, result: decisionForm.result })
  } else {
    await adminPortalService.updateItem('arbitrations', activeCase.value.caseNo, { status: decisionForm.status, result: decisionForm.result })
  }
  decisionDialogVisible.value = false
  ElMessage.success('处理结果已提交并留痕')
  await loadPortalData()
}

async function publishRules() {
  await ElMessageBox.confirm('规则修改将实时生效，确认发布？', '二次确认', {
    type: 'warning',
    confirmButtonText: '发布',
    cancelButtonText: '取消',
  })
  await adminPortalService.updateRules(JSON.parse(JSON.stringify(rulesState)))
  ElMessage.success('规则已发布')
  await loadPortalData()
}

async function requestPenaltyRuleChange() {
  const { value } = await ElMessageBox.prompt('请填写处罚规则变更原因、风险评估或业务背景', '处罚规则变更申请', {
    confirmButtonText: '提交申请',
    cancelButtonText: '取消',
    inputType: 'textarea',
    inputPlaceholder: '例如：某城市近期客户爽约率异常，需要评估是否调整预警阈值。',
  })
  await adminPortalService.createRuleChangeRequest({ scope: '处罚规则', reason: value })
  ElMessage.success('变更申请已提交，处罚底层逻辑未被直接修改')
  await loadPortalData()
}

function openFrontendComplaint() {
  router.push('/complaints/new')
}
</script>

<style scoped>
.admin-portal {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 248px 1fr;
  background: #f4f6f8;
  color: #1f2937;
}

.portal-sidebar {
  background: #111827;
  color: #f9fafb;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: sticky;
  top: 0;
  height: 100vh;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 6px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #2563eb;
  font-weight: 800;
  font-size: 20px;
}

.brand h1,
.brand p,
.panel-toolbar h3,
.panel-toolbar p {
  margin: 0;
}

.brand h1 {
  font-size: 16px;
}

.brand p,
.security-panel p,
.eyebrow,
.panel-toolbar p,
.metric-card p {
  color: #6b7280;
  font-size: 13px;
}

.module-menu {
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #d1d5db;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.08);
  --el-menu-active-color: #ffffff;
  border-right: 0;
}

.module-menu :deep(.el-menu-item) {
  border-radius: 8px;
  margin-bottom: 4px;
}

.module-menu :deep(.el-menu-item.is-active) {
  background: #2563eb;
}

.menu-badge {
  margin-left: auto;
}

.security-panel {
  margin-top: auto;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
}

.security-panel span,
.security-panel strong {
  display: block;
}

.security-panel span {
  color: #9ca3af;
  font-size: 12px;
}

.security-panel strong {
  margin-top: 4px;
  font-size: 14px;
}

.portal-main {
  min-width: 0;
  padding: 18px 22px 28px;
}

.portal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.portal-header h2 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: grid;
  grid-template-columns: minmax(260px, 360px) auto auto;
  align-items: center;
  gap: 10px;
}

.module-tabs {
  margin-bottom: 12px;
}

.panel,
.panel-block {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.panel-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
}

.panel-toolbar h3 {
  font-size: 18px;
}

.toolbar-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 12px;
}

.toolbar-actions .el-select {
  width: 140px;
}

.status-grid,
.metric-grid,
.dashboard-grid {
  display: grid;
  gap: 12px;
  margin-bottom: 14px;
}

.status-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.dashboard-grid {
  grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr);
}

.stat-card,
.metric-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  background: #ffffff;
}

.stat-card span,
.metric-card span {
  color: #6b7280;
  font-size: 13px;
}

.stat-card strong,
.metric-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  color: #111827;
}

.metric-card .danger {
  color: #dc2626;
}

.rank-row {
  display: grid;
  grid-template-columns: 80px 1fr 48px;
  align-items: center;
  gap: 10px;
  margin: 12px 0;
}

.trend-chart {
  height: 170px;
  display: flex;
  align-items: flex-end;
  gap: 18px;
  padding: 16px 8px 4px;
  border-bottom: 1px solid #e5e7eb;
}

.trend-bar {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  position: relative;
  height: 140px;
}

.trend-bar i,
.trend-bar b {
  width: 14px;
  border-radius: 4px 4px 0 0;
  display: block;
}

.trend-bar i {
  background: #2563eb;
}

.trend-bar b {
  background: #10b981;
}

.trend-bar span {
  position: absolute;
  bottom: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}

.funnel {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.funnel div {
  height: 38px;
  display: grid;
  place-items: center;
  background: #2563eb;
  color: #ffffff;
  border-radius: 6px;
  font-weight: 700;
}

.rules-form {
  max-width: 820px;
}

.policy-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.policy-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  background: #f9fafb;
}

.policy-card span {
  color: #6b7280;
  font-size: 13px;
}

.policy-card strong {
  display: block;
  margin: 8px 0;
  font-size: 18px;
  color: #111827;
}

.policy-card p,
.policy-lock p {
  margin: 0;
  color: #4b5563;
  line-height: 1.7;
}

.policy-lock {
  margin-top: 14px;
  display: grid;
  gap: 10px;
  max-width: 720px;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
}

@media (max-width: 1180px) {
  .admin-portal {
    grid-template-columns: 220px 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-grid,
  .status-grid,
  .policy-grid {
    grid-template-columns: 1fr 1fr;
  }

  .header-actions {
    grid-template-columns: 1fr auto;
  }
}

@media (max-width: 860px) {
  .admin-portal {
    grid-template-columns: 1fr;
  }

  .portal-sidebar {
    position: static;
    height: auto;
  }

  .portal-header,
  .panel-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions,
  .metric-grid,
  .dashboard-grid,
  .status-grid,
  .policy-grid {
    grid-template-columns: 1fr;
  }
}
</style>
