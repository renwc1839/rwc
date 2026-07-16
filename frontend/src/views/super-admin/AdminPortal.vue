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
        <span>权限与审计</span>
        <strong>敏感数据二次验证</strong>
        <p>处理动作统一写入不可删除操作日志</p>
      </div>
    </aside>

    <main class="portal-main">
      <header class="portal-header">
        <div>
          <p class="eyebrow">境外租房平台运营管理</p>
          <h2>{{ currentModule?.label }}</h2>
        </div>
        <div class="header-actions">
          <el-input v-model="globalKeyword" :prefix-icon="Search" placeholder="搜索预约、房源、投诉、工单、人员" clearable />
          <el-button :icon="Refresh" :loading="loading" @click="loadPortalData">刷新</el-button>
          <el-button type="primary" @click="openFrontendComplaint">前台投诉入口</el-button>
        </div>
      </header>

      <section class="module-tabs">
        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane v-for="tab in currentTabs" :key="tab.key" :label="tab.label" :name="tab.key" />
        </el-tabs>
      </section>

      <section class="content-shell" v-loading="loading">
        <template v-if="activeModule === 'dashboard'">
          <div v-if="activeTab === 'realtime-dashboard'" class="panel">
            <PanelTitle title="实时大盘" desc="登录后先看今日预约、工单、投诉、财务和预警，不做规则编辑。" />
            <div class="metric-grid">
              <button v-for="metric in metrics" :key="metric.label" class="metric-card" :class="{ danger: metric.danger }" @click="jumpFromMetric(metric.label)">
                <span>{{ metric.label }}</span>
                <strong>{{ metric.value }}</strong>
                <p>{{ metric.hint }}</p>
              </button>
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

          <div v-else class="panel">
            <PanelTitle title="数据报表" desc="从真实预约、投诉、签约、人员负载和房源状态做运营统计。" />
            <div class="toolbar-actions">
              <el-button @click="recordAction('report.generate', 'report', '已生成当前筛选报表')">生成报表</el-button>
              <el-button type="primary" @click="recordAction('report.export', 'report', '已提交导出审批')">申请导出</el-button>
            </div>
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
            <div class="report-grid">
              <div>
                <h3>报表生成记录</h3>
                <el-table :data="reports" border stripe>
                  <el-table-column prop="id" label="报表号" width="110" />
                  <el-table-column prop="name" label="名称" />
                  <el-table-column prop="source" label="数据来源" min-width="220" />
                  <el-table-column prop="createdAt" label="生成时间" min-width="170" />
                  <el-table-column label="状态" width="100">
                    <template #default="{ row }"><el-tag type="success">{{ row.status }}</el-tag></template>
                  </el-table-column>
                </el-table>
              </div>
              <div>
                <h3>导出审批记录</h3>
                <el-table :data="exportRequests" border stripe>
                  <el-table-column prop="id" label="申请号" width="110" />
                  <el-table-column prop="name" label="名称" />
                  <el-table-column prop="scope" label="导出范围" min-width="220" />
                  <el-table-column prop="createdAt" label="申请时间" min-width="170" />
                  <el-table-column label="状态" width="100">
                    <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </template>

        <template v-else-if="activeModule === 'calendar'">
          <div v-if="activeTab === 'calendar-view'" class="panel">
            <PanelTitle title="统一日历 / 预约日历" desc="用日历视图把预约、带看、锁定冲突放在同一张运营视图里。" />
            <div class="calendar-board">
              <div v-for="day in calendarDays" :key="day.date" class="day-cell">
                <span>{{ day.week }}</span>
                <strong>{{ day.date }}</strong>
                <p>{{ day.count }} 个事项</p>
                <em v-for="event in day.events" :key="event">{{ event }}</em>
              </div>
            </div>
          </div>

          <div v-else class="panel">
            <PanelTitle title="预约调度" desc="分配对接人、推进待确认/带看中/签约/取消状态，形成可追踪流转。" />
            <div class="toolbar-actions">
              <el-select v-model="filters.city" placeholder="城市" clearable>
                <el-option v-for="city in cities" :key="city" :label="city" :value="city" />
              </el-select>
              <el-button type="primary" :icon="UserFilled" @click="bulkAssign">分配最早待办</el-button>
            </div>
            <el-table :data="filteredAppointments" border stripe>
              <el-table-column prop="id" label="编号" width="110" sortable />
              <el-table-column prop="customer" label="客户" width="110" />
              <el-table-column prop="phone" label="联系方式" width="130" />
              <el-table-column prop="property" label="意向房源" min-width="210" />
              <el-table-column prop="time" label="预约时间" min-width="150" sortable />
              <el-table-column prop="city" label="城市" width="90" />
              <el-table-column prop="assignee" label="对接人" width="100" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="300">
                <template #default="{ row }">
                  <el-button size="small" @click="assignAppointment(row)">分配</el-button>
                  <el-button size="small" @click="updateItem('appointments', row.id, '带看中')">带看中</el-button>
                  <el-button size="small" type="success" @click="updateItem('appointments', row.id, '已签约')">签约</el-button>
                  <el-button size="small" type="danger" @click="updateItem('appointments', row.id, '已取消')">取消</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'workorders'">
          <div v-if="activeTab === 'task-flow'" class="panel">
            <PanelTitle title="工单 / 任务管理" desc="投诉、维修、带看反馈都进入工单流，能指派、处理、结案。" />
            <el-table :data="filteredWorkOrders" border stripe>
              <el-table-column prop="id" label="工单号" width="120" sortable />
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="title" label="任务内容" min-width="240" />
              <el-table-column prop="owner" label="负责人" width="110" />
              <el-table-column prop="related" label="关联对象" width="120" />
              <el-table-column prop="deadline" label="截止时间" width="120" />
              <el-table-column label="优先级" width="90">
                <template #default="{ row }"><el-tag :type="warningType(row.priority)">{{ row.priority }}</el-tag></template>
              </el-table-column>
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="230">
                <template #default="{ row }">
                  <el-button size="small" @click="openProcess(row, 'workOrders', '处理工单')">处理</el-button>
                  <el-button size="small" type="success" @click="updateItem('workOrders', row.id, '已完结')">结案</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else class="panel">
            <PanelTitle title="异常督办" desc="今日待办、超时提醒和管理员介入集中在这里，不再散落各处。" />
            <el-table :data="filteredExceptions" border stripe>
              <el-table-column prop="type" label="异常类型" min-width="150" />
              <el-table-column prop="target" label="关联对象" min-width="180" />
              <el-table-column prop="owner" label="负责人" width="100" />
              <el-table-column prop="elapsed" label="超时" width="100" />
              <el-table-column label="级别" width="90">
                <template #default="{ row }"><el-tag :type="warningType(row.level)">{{ row.level }}</el-tag></template>
              </el-table-column>
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="250">
                <template #default="{ row }">
                  <el-button size="small" @click="recordAction('exception.remind', row.id, `已催办 ${row.owner}`)">催办</el-button>
                  <el-button size="small" @click="updateItem('exceptions', row.id, '已转派')">转派</el-button>
                  <el-button size="small" type="warning" @click="updateItem('exceptions', row.id, '管理员介入')">介入</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'messages'">
          <div class="panel">
            <PanelTitle title="统一消息中心" desc="投诉、预约、对接人反馈集中记录，后续可以扩展短信/站内信/邮件。" />
            <el-table :data="filteredMessages" border stripe>
              <el-table-column prop="id" label="消息号" width="120" />
              <el-table-column prop="channel" label="来源" width="100" />
              <el-table-column prop="sender" label="发送人" width="110" />
              <el-table-column prop="target" label="接收人" width="110" />
              <el-table-column prop="summary" label="内容摘要" min-width="260" />
              <el-table-column prop="related" label="关联对象" width="120" />
              <el-table-column prop="createdAt" label="时间" min-width="170" />
              <el-table-column label="状态" width="90">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }"><el-button size="small" @click="updateItem('messages', row.id, '已读')">标记已读</el-button></template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'properties'">
          <div class="panel">
            <PanelTitle title="房源状态管理" desc="房源按可租、锁定、带看中、签约、下架完整流转，冲突可见。" />
            <div class="status-grid">
              <div v-for="item in propertyStatusCards" :key="item.label" class="stat-card">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <el-table :data="filteredProperties" border stripe>
              <el-table-column prop="title" label="房源" min-width="220" />
              <el-table-column prop="city" label="城市" width="90" />
              <el-table-column prop="landlord" label="房东" width="120" />
              <el-table-column prop="lockedUntil" label="锁定到期" min-width="140" />
              <el-table-column prop="conflicts" label="冲突" width="80" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="320">
                <template #default="{ row }">
                  <el-button size="small" @click="updateItem('properties', row.id, '可租')">可租</el-button>
                  <el-button size="small" @click="updateItem('properties', row.id, '已预约')">锁定</el-button>
                  <el-button size="small" @click="updateItem('properties', row.id, '带看中')">带看中</el-button>
                  <el-button size="small" type="success" @click="updateItem('properties', row.id, '已签约')">签约</el-button>
                  <el-button size="small" type="danger" @click="updateItem('properties', row.id, '已下架')">下架</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'staff'">
          <div class="panel">
            <PanelTitle title="人员负载 / 排班" desc="把当前负载、今日待办、超时提醒和跨城支援放在同一张人员表。" />
            <el-table :data="filteredStaff" border stripe>
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="city" label="负责城市" width="110" />
              <el-table-column prop="workTime" label="排班" width="140" />
              <el-table-column label="负载" min-width="180">
                <template #default="{ row }"><el-progress :percentage="Number(row.load || 0)" :status="Number(row.load || 0) >= 80 ? 'exception' : undefined" /></template>
              </el-table-column>
              <el-table-column prop="pending" label="今日待办" width="100" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="250">
                <template #default="{ row }">
                  <el-button size="small" @click="updateItem('staff', row.id, '在岗')">在岗</el-button>
                  <el-button size="small" @click="updateItem('staff', row.id, '跨城支援')">跨城支援</el-button>
                  <el-button size="small" type="warning" @click="updateItem('staff', row.id, '休息')">休息</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'complaints'">
          <div class="panel">
            <PanelTitle title="投诉闭环" desc="只做投诉提交、指派核实、处理记录、结案结果和举证材料入口，不再定义为仲裁。" />
            <div class="toolbar-actions">
              <el-button type="primary" @click="openFrontendComplaint">打开前台提交页</el-button>
            </div>
            <el-table :data="filteredComplaints" border stripe>
              <el-table-column prop="id" label="投诉号" width="120" sortable />
              <el-table-column prop="category" label="分类" width="110" />
              <el-table-column prop="title" label="投诉内容" min-width="230" />
              <el-table-column prop="complainantName" label="提交人" width="110" />
              <el-table-column prop="contact" label="联系方式" width="130" />
              <el-table-column prop="city" label="城市" width="90" />
              <el-table-column prop="property" label="关联房源" min-width="180" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="250">
                <template #default="{ row }">
                  <el-button size="small" @click="openProcess(row, 'complaints', '处理投诉')">处理</el-button>
                  <el-button size="small" type="success" @click="finishComplaint(row)">结案</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else-if="activeModule === 'finance'">
          <div class="panel">
            <PanelTitle title="押金 / 财务" desc="先做押金金额、退款/扣款处理和凭证记录，不做争议裁定结论。" />
            <el-table :data="filteredFinanceItems" border stripe>
              <el-table-column prop="id" label="单号" width="120" />
              <el-table-column prop="type" label="类型" width="110" />
              <el-table-column prop="customer" label="客户" width="110" />
              <el-table-column prop="property" label="房源" min-width="220" />
              <el-table-column prop="amount" label="金额" width="110" />
              <el-table-column prop="evidence" label="凭证材料" min-width="220" />
              <el-table-column prop="owner" label="负责人" width="110" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="260">
                <template #default="{ row }">
                  <el-button size="small" @click="openProcess(row, 'financeItems', '处理财务单')">处理</el-button>
                  <el-button size="small" type="success" @click="updateItem('financeItems', row.id, row.type === '押金退款' ? '已退款' : '已扣款')">
                    {{ row.type === '押金退款' ? '退款完成' : '扣款完成' }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <template v-else>
          <div v-if="activeTab === 'accounts-permissions'" class="panel">
            <PanelTitle title="账号权限" desc="按按钮权限、角色、账号启停管理后台入口；超级管理员不可删除。" />
            <el-table :data="filteredAccounts" border stripe>
              <el-table-column prop="name" label="账号" />
              <el-table-column prop="role" label="角色" />
              <el-table-column prop="phone" label="手机号" />
              <el-table-column label="二次验证">
                <template #default="{ row }"><el-tag :type="row.twoFactor ? 'success' : 'warning'">{{ row.twoFactor ? '已启用' : '未启用' }}</el-tag></template>
              </el-table-column>
              <el-table-column label="状态">
                <template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" width="180">
                <template #default="{ row }">
                  <el-button size="small" @click="updateItem('accounts', row.id, row.status === '启用' ? '禁用' : '启用')">
                    {{ row.status === '启用' ? '禁用' : '启用' }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-else class="panel">
            <PanelTitle title="操作日志" desc="所有后台操作只可查看，不提供删除和修改入口。" />
            <el-table :data="filteredLogs" border stripe>
              <el-table-column prop="operator" label="操作人" width="110" />
              <el-table-column prop="time" label="操作时间" min-width="170" />
              <el-table-column prop="type" label="类型" width="130" />
              <el-table-column prop="target" label="对象" width="130" />
              <el-table-column prop="content" label="内容" min-width="280" />
              <el-table-column prop="ip" label="IP 地址" width="120" />
            </el-table>
          </div>
        </template>
      </section>
    </main>

    <el-dialog v-model="processDialogVisible" :title="processDialogTitle" width="560px">
      <el-form label-position="top">
        <el-form-item label="处理对象">
          <el-input :model-value="activeRecord?.id || activeRecord?.related || ''" disabled />
        </el-form-item>
        <el-form-item label="当前内容">
          <el-input :model-value="activeRecord?.title || activeRecord?.summary || activeRecord?.evidence || ''" disabled />
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="processForm.status">
            <el-option v-for="option in processStatusOptions" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理记录">
          <el-input v-model="processForm.result" type="textarea" :rows="4" placeholder="填写指派核实人、处理过程、凭证说明或结案结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="processDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitProcess">提交并留痕</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Calendar,
  ChatDotRound,
  DataAnalysis,
  House,
  Lock,
  Refresh,
  Search,
  Tickets,
  UserFilled,
  Wallet,
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
const processDialogVisible = ref(false)
const processDialogTitle = ref('处理记录')
const activeRecord = ref<any | null>(null)
const activeCollection = ref('')
const processForm = reactive({ status: '处理中', result: '' })

const modules = [
  {
    key: 'dashboard',
    label: '数据看板',
    icon: DataAnalysis,
    tabs: [
      { key: 'realtime-dashboard', label: '实时大盘' },
      { key: 'reports', label: '报表统计' },
    ],
  },
  {
    key: 'calendar',
    label: '运营日历',
    icon: Calendar,
    badge: 3,
    tabs: [
      { key: 'calendar-view', label: '统一日历' },
      { key: 'appointments', label: '预约调度' },
    ],
  },
  {
    key: 'workorders',
    label: '工单中心',
    icon: Tickets,
    badge: 5,
    tabs: [
      { key: 'task-flow', label: '工单任务' },
      { key: 'exceptions', label: '异常督办' },
    ],
  },
  { key: 'messages', label: '统一消息', icon: ChatDotRound, badge: 2, tabs: [{ key: 'message-center', label: '消息记录' }] },
  { key: 'properties', label: '房源状态', icon: House, tabs: [{ key: 'property-status', label: '状态流转' }] },
  { key: 'staff', label: '人员排班', icon: UserFilled, tabs: [{ key: 'staff-load', label: '负载排班' }] },
  { key: 'complaints', label: '投诉闭环', icon: Tickets, badge: 1, tabs: [{ key: 'complaint-flow', label: '投诉处理' }] },
  { key: 'finance', label: '押金财务', icon: Wallet, badge: 2, tabs: [{ key: 'deposit-finance', label: '财务处理' }] },
  {
    key: 'audit',
    label: '权限审计',
    icon: Lock,
    tabs: [
      { key: 'accounts-permissions', label: '账号权限' },
      { key: 'operation-logs', label: '操作日志' },
    ],
  },
]

const appointments = ref<any[]>([])
const properties = ref<any[]>([])
const staff = ref<any[]>([])
const exceptions = ref<any[]>([])
const complaints = ref<any[]>([])
const workOrders = ref<any[]>([])
const messages = ref<any[]>([])
const financeItems = ref<any[]>([])
const warnings = ref<any[]>([])
const accounts = ref<any[]>([])
const logs = ref<any[]>([])
const reports = ref<any[]>([])
const exportRequests = ref<any[]>([])
const actionHistory = ref<any[]>([])
const metrics = ref<any[]>([])
const cityRankRows = ref<any[]>([])
const trendRows = ref<any[]>([])
const settings = reactive<any>({ platformName: '', servicePhone: '', cities: [] })

const businessRows = computed(() => {
  const citySet = new Set([...settings.cities, ...properties.value.map((item) => item.city), ...appointments.value.map((item) => item.city)].filter(Boolean))
  return Array.from(citySet).map((city) => {
    const cityProperties = properties.value.filter((item) => item.city === city)
    const cityBookings = appointments.value.filter((item) => item.city === city)
    const contracts = cityBookings.filter((item) => item.status === '已签约').length + cityProperties.filter((item) => item.status === '已签约').length
    const conversion = cityBookings.length ? `${Math.round((contracts / cityBookings.length) * 1000) / 10}%` : '0%'
    return { city, properties: cityProperties.length, bookings: cityBookings.length, contracts, conversion }
  })
})
const funnelRows = computed(() => {
  const booking = appointments.value.length
  const visit = appointments.value.filter((item) => ['已确认', '带看中', '已签约'].includes(item.status)).length
  const sign = appointments.value.filter((item) => item.status === '已签约').length + properties.value.filter((item) => item.status === '已签约').length
  const browse = Math.max(properties.value.length * 120 + booking * 20, booking, 1)
  const width = (value: number) => Math.max(18, Math.round((value / browse) * 100))
  return [
    { label: '浏览', value: browse, width: 100 },
    { label: '预约', value: booking, width: width(booking) },
    { label: '带看', value: visit, width: width(visit) },
    { label: '签约', value: sign, width: width(sign) },
  ]
})

const currentModule = computed(() => modules.find((item) => item.key === activeModule.value))
const currentTabs = computed(() => currentModule.value?.tabs || [])
const cities = computed(() => Array.from(new Set([...settings.cities, ...properties.value.map((item) => item.city)].filter(Boolean))))
const keyword = computed(() => globalKeyword.value.trim().toLowerCase())
const filteredAppointments = computed(() => appointments.value.filter((item) => (!filters.city || item.city === filters.city) && matchKeyword(item)))
const filteredProperties = computed(() => properties.value.filter(matchKeyword))
const filteredStaff = computed(() => staff.value.filter(matchKeyword))
const filteredComplaints = computed(() => complaints.value.filter(matchKeyword))
const filteredWorkOrders = computed(() => workOrders.value.filter(matchKeyword))
const filteredMessages = computed(() => messages.value.filter(matchKeyword))
const filteredFinanceItems = computed(() => financeItems.value.filter(matchKeyword))
const filteredExceptions = computed(() => exceptions.value.filter(matchKeyword))
const filteredAccounts = computed(() => accounts.value.filter(matchKeyword))
const filteredLogs = computed(() => logs.value.filter(matchKeyword))
const propertyStatusCards = computed(() =>
  ['可租', '已预约', '带看中', '已签约', '已下架'].map((label) => ({
    label,
    value: properties.value.filter((item) => item.status === label).length,
  })),
)
const calendarDays = computed(() => {
  const base = [
    { week: '周一', date: '07/06' },
    { week: '周二', date: '07/07' },
    { week: '周三', date: '07/08' },
    { week: '周四', date: '07/09' },
    { week: '周五', date: '07/10' },
    { week: '周六', date: '07/11' },
    { week: '周日', date: '07/12' },
  ]
  return base.map((day, index) => {
    const events = appointments.value.slice(index, index + 2).map((item) => `${item.time?.slice(11) || ''} ${item.property}`)
    if (index === 2) events.push('锁定冲突 2')
    return { ...day, events, count: events.length }
  })
})
const processStatusOptions = computed(() => {
  if (activeCollection.value === 'financeItems') return ['待审核', '处理中', '已退款', '已扣款', '已完结']
  if (activeCollection.value === 'complaints') return ['待处理', '处理中', '已完结', '已驳回']
  return ['待处理', '处理中', '已完结', '已转派', '已驳回']
})

onMounted(loadPortalData)

function matchKeyword(item: any) {
  if (!keyword.value) return true
  return JSON.stringify(item).toLowerCase().includes(keyword.value)
}

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
  workOrders.value = state.workOrders || []
  messages.value = state.messages || []
  financeItems.value = state.financeItems || []
  warnings.value = state.warnings || []
  accounts.value = state.accounts || []
  logs.value = state.logs || []
  reports.value = state.reports || []
  exportRequests.value = state.exportRequests || []
  actionHistory.value = state.actionHistory || []
  Object.assign(settings, state.settings || {})
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
  if (['已确认', '可租', '已签约', '启用', '已完结', '已处理', '已退款', '已扣款', '已读'].includes(status)) return 'success'
  if (['待分配', '待确认', '待处理', '待审核', '未读'].includes(status)) return 'warning'
  if (['处理中', '已预约', '带看中', '管理员介入', '跨城支援', '已转派', '在岗'].includes(status)) return 'primary'
  if (['已取消', '已驳回', '已下架', '禁用', '休息'].includes(status)) return 'danger'
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
  const target = appointments.value.find((item) => item.status === '待分配') || appointments.value[0]
  if (target) await assignAppointment(target)
}

async function updateItem(collection: string, id: string, status: string, result?: string) {
  await adminPortalService.updateItem(collection, id, { status, result })
  ElMessage.success('状态已更新并写入日志')
  await loadPortalData()
}

function openProcess(row: any, collection: string, title: string) {
  activeRecord.value = row
  activeCollection.value = collection
  processDialogTitle.value = title
  processForm.status = row.status === '待处理' ? '处理中' : row.status
  processForm.result = row.result || ''
  processDialogVisible.value = true
}

async function submitProcess() {
  if (!activeRecord.value) return
  if (!processForm.result.trim()) {
    ElMessage.error('请填写处理记录')
    return
  }
  if (activeCollection.value === 'complaints') {
    await adminPortalService.updateComplaint(activeRecord.value.id, { status: processForm.status, result: processForm.result })
  } else {
    await updateItem(activeCollection.value, activeRecord.value.id, processForm.status, processForm.result)
  }
  processDialogVisible.value = false
  ElMessage.success('处理记录已提交')
  await loadPortalData()
}

async function finishComplaint(row: any) {
  await adminPortalService.updateComplaint(row.id, { status: '已完结', result: row.result || '投诉已处理并结案。' })
  ElMessage.success('投诉已结案')
  await loadPortalData()
}

function jumpFromMetric(label: string) {
  if (label.includes('投诉')) selectModule('complaints')
  else if (label.includes('工单')) selectModule('workorders')
  else if (label.includes('押金') || label.includes('财务')) selectModule('finance')
  else if (label.includes('预警')) {
    selectModule('workorders')
    activeTab.value = 'exceptions'
  } else selectModule('calendar')
}

async function recordAction(action: string, target: string, content: string) {
  await adminPortalService.recordAction({ action, target, content })
  ElMessage.success(content)
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

.metric-grid,
.dashboard-grid,
.status-grid,
.calendar-board {
  display: grid;
  gap: 12px;
  margin-bottom: 14px;
}

.metric-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.dashboard-grid {
  grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr);
}

.status-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.calendar-board {
  grid-template-columns: repeat(7, minmax(132px, 1fr));
}

.metric-card {
  text-align: left;
  cursor: pointer;
}

.metric-card,
.stat-card,
.day-cell {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  background: #ffffff;
}

.metric-card.danger {
  border-color: #fecaca;
  background: #fff7f7;
}

.metric-card span,
.stat-card span,
.day-cell span {
  color: #6b7280;
  font-size: 13px;
}

.metric-card strong,
.stat-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  color: #111827;
}

.day-cell strong {
  display: block;
  margin-top: 6px;
  font-size: 18px;
}

.day-cell p {
  margin: 8px 0;
  color: #4b5563;
  font-size: 13px;
}

.day-cell em {
  display: block;
  margin-top: 6px;
  padding: 6px 8px;
  border-radius: 6px;
  background: #eef2ff;
  color: #3730a3;
  font-size: 12px;
  font-style: normal;
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

.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 18px;
}

.report-grid h3 {
  margin: 0 0 10px;
  font-size: 15px;
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
  .report-grid,
  .calendar-board {
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
  .report-grid,
  .calendar-board {
    grid-template-columns: 1fr;
  }
}
</style>
