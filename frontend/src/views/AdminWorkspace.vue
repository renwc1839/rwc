<template>
  <div class="workspace-page">
    <!-- ===== 顶部用户信息头部 ===== -->
    <el-card shadow="never" class="user-card">
      <div class="user-info">
        <el-avatar :size="64" :icon="UserFilled" />
        <div class="user-detail">
          <div class="user-name-row">
            <span class="user-name">{{ adminName }}</span>
            <el-tag :type="roleTagType" size="small" effect="dark">{{ roleLabel }}</el-tag>
            <el-tag v-if="verified" type="success" size="small">✓ 企业认证</el-tag>
            <el-tag v-else type="warning" size="small">待认证</el-tag>
          </div>
          <div class="user-contact">
            <span>📧 {{ adminEmail }}</span>
            <span>📱 {{ adminPhone }}</span>
            <span>🏢 负责片区：{{ adminDistrict }}</span>
            <span>📅 注册于 {{ adminSince }}</span>
          </div>
        </div>
        <div class="user-actions">
          <el-button type="primary" round @click="showEditProfile = true">编辑资料</el-button>
          <el-button round @click="showUploadQualification = true">资质上传</el-button>
        </div>
      </div>
    </el-card>

    <!-- ===== 统计卡片 ===== -->
    <div class="stats-grid">
      <div class="stat-card" v-for="s in statsCards" :key="s.label" @click="activeTab = s.tab">
        <span class="stat-icon">{{ s.icon }}</span>
        <div class="stat-info">
          <div class="stat-num">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-sub" v-if="s.sub">{{ s.sub }}</div>
        </div>
      </div>
    </div>

    <!-- ===== Tab 主体 ===== -->
    <el-card shadow="never" class="tabs-card">
      <el-tabs v-model="activeTab" class="workspace-tabs" type="border-card">
        <!-- Tab1: 托管房源管理 -->
        <el-tab-pane v-if="canViewProperties" label="🏠 房源管理" name="properties">
          <div class="tab-toolbar">
            <el-radio-group v-model="propertyFilter" size="small">
              <el-radio-button value="all">全部 ({{ propertyRows.length }})</el-radio-button>
              <el-radio-button value="vacant">空置 ({{ vacantCount }})</el-radio-button>
              <el-radio-button value="rented">已出租 ({{ rentedCount }})</el-radio-button>
              <el-radio-button value="maintenance">维护中</el-radio-button>
              <el-radio-button value="pending">待上架</el-radio-button>
            </el-radio-group>
            <div>
              <el-button type="primary" size="small" @click="handleBatchAdd">批量新增</el-button>
              <el-button size="small" @click="handleBatchPublish">批量上架</el-button>
              <el-button size="small" type="warning" @click="handleBatchOffline">批量下架</el-button>
            </div>
          </div>
          <el-table :data="filteredProperties" stripe>
            <el-table-column type="selection" width="40" />
            <el-table-column label="地址" prop="address" min-width="180" />
            <el-table-column label="户型" width="90">
              <template #default="{ row }">{{ row.bedrooms }}室{{ row.bathrooms }}卫</template>
            </el-table-column>
            <el-table-column label="月租" width="100">
              <template #default="{ row }">¥{{ row.price }}</template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="负责人" width="180">
              <template #default="{ row }">
                <el-select
                  v-if="isAdmin"
                  :model-value="row.propertyManagerId || ''"
                  size="small"
                  placeholder="未分配"
                  clearable
                  @change="(value: number | string) => assignPropertyManager(row, value)"
                >
                  <el-option
                    v-for="manager in propertyManagerOptions"
                    :key="manager.id"
                    :label="manager.username"
                    :value="manager.id"
                  />
                </el-select>
                <span v-else>{{ row.propertyManagerName }}</span>
              </template>
            </el-table-column>
            <el-table-column label="当前租客" width="100" prop="tenant" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" text type="primary" @click="editProperty(row)">编辑</el-button>
                <el-button size="small" text type="warning" @click="maintainProperty(row)">维修</el-button>
                <el-button size="small" text @click="viewPropertyBookings(row)">预约记录</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab2: 看房预约管理 -->
        <el-tab-pane v-if="canViewBookings" label="📅 预约管理" name="bookings">
          <div class="tab-toolbar">
            <el-radio-group v-model="bookingFilter" size="small">
              <el-radio-button value="all">全部 ({{ bookings.length }})</el-radio-button>
              <el-radio-button value="pending">待审核 ({{ pendingBookingCount }})</el-radio-button>
              <el-radio-button value="approved">已同意</el-radio-button>
              <el-radio-button value="rejected">已拒绝</el-radio-button>
              <el-radio-button value="cancelled">已取消</el-radio-button>
            </el-radio-group>
            <div>
              <el-button type="primary" size="small" @click="handleBatchRemind">批量发送提醒</el-button>
            </div>
          </div>
          <el-table :data="filteredBookings" stripe>
            <el-table-column label="房源" prop="property" min-width="160" />
            <el-table-column label="租客" prop="tenant" width="100" />
            <el-table-column label="手机" prop="phone" width="120" />
            <el-table-column label="预约时间" prop="date" width="110" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="bookingStatusTag(row.status)" size="small">{{ row.statusText }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240">
              <template #default="{ row }">
                <el-button v-if="row.status === 'pending'" size="small" type="success" @click="approveBooking(row)">确认</el-button>
                <el-button v-if="row.status === 'pending'" size="small" type="danger" @click="rejectBooking(row)">驳回</el-button>
                <el-button size="small" text @click="viewTenantInfo(row)">租客信息</el-button>
                <el-button size="small" text type="warning" @click="markVisited(row)">已接待</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab3: 租赁合约管理 -->
        <el-tab-pane v-if="canViewAdminTabs" label="📄 合约管理" name="contracts">
          <div class="tab-toolbar">
            <el-radio-group v-model="contractFilter" size="small">
              <el-radio-button value="active">生效中 ({{ activeContractCount }})</el-radio-button>
              <el-radio-button value="expiring">即将到期</el-radio-button>
              <el-radio-button value="renewal">待续签</el-radio-button>
              <el-radio-button value="deposit">待签约定金</el-radio-button>
              <el-radio-button value="terminated">已解约</el-radio-button>
            </el-radio-group>
            <div>
              <el-button type="primary" size="small" @click="batchGenerateContracts">批量生成合同</el-button>
              <el-button size="small" @click="batchExportContracts">批量导出</el-button>
              <el-button size="small" type="warning" @click="batchRenewContracts">批量续租</el-button>
            </div>
          </div>
          <el-table :data="filteredContracts" stripe>
            <el-table-column label="合同编号" width="140" prop="id" />
            <el-table-column label="房源" prop="property" min-width="160" />
            <el-table-column label="租客" prop="tenant" width="100" />
            <el-table-column label="租期" width="180">
              <template #default="{ row }">{{ row.startDate }} ~ {{ row.endDate }}</template>
            </el-table-column>
            <el-table-column label="月租金" width="100" prop="rent" />
            <el-table-column label="押金" width="90" prop="deposit" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === '生效中' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button size="small" text type="primary" @click="viewContract(row)">查看</el-button>
                <el-button size="small" text type="danger" @click="terminateContract(row)">解约</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab4: 财务收支 -->
        <el-tab-pane v-if="canViewAdminTabs" label="💰 财务中心" name="finance">
          <el-row :gutter="16" class="finance-summary">
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="本月应收" :value="98500" prefix="¥" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="已收租金" :value="76200" prefix="¥" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="定金收入" :value="24500" prefix="¥" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="逾期未缴" :value="3" suffix="户"><template #suffix><el-tag type="danger" size="small">待催缴</el-tag></template></el-statistic></el-card></el-col>
          </el-row>
          <div class="tab-toolbar">
            <el-radio-group v-model="financeTab" size="small">
              <el-radio-button value="deposit">定金订单</el-radio-button>
              <el-radio-button value="rent">月度租金</el-radio-button>
              <el-radio-button value="ledger">收支明细</el-radio-button>
              <el-radio-button value="withdraw">提现管理</el-radio-button>
            </el-radio-group>
            <el-button type="primary" size="small">导出月度报表</el-button>
          </div>
          <el-table :data="financeData" stripe>
            <el-table-column label="流水号" prop="id" width="160" />
            <el-table-column label="类型" prop="type" width="100" />
            <el-table-column label="关联房源" prop="property" min-width="140" />
            <el-table-column label="租客" prop="tenant" width="90" />
            <el-table-column label="金额" prop="amount" width="110" />
            <el-table-column label="时间" prop="date" width="110" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === '已到账' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab5: 在住租客 -->
        <el-tab-pane v-if="canViewAdminTabs" label="👥 租客管理" name="tenants">
          <el-table :data="tenantRows" stripe>
            <el-table-column label="租客" prop="name" width="100" />
            <el-table-column label="手机" prop="phone" width="130" />
            <el-table-column label="入住房源" prop="property" min-width="160" />
            <el-table-column label="合同编号" prop="contractId" width="140" />
            <el-table-column label="月租金" prop="rent" width="100" />
            <el-table-column label="缴费状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.payStatus === '正常' ? 'success' : 'warning'" size="small">{{ row.payStatus }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="租期到期" prop="endDate" width="110" />
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button size="small" text type="primary" @click="viewTenantDetail(row)">详情</el-button>
                <el-button size="small" text @click="viewTenantPayments(row)">缴费记录</el-button>
                <el-button size="small" text type="warning" @click="viewTenantRepairs(row)">报修</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab6: 维修工单 -->
        <el-tab-pane v-if="canViewRepairs" label="🔧 维修工单" name="repairs">
          <div class="repair-summary">
            <div>
              <strong>{{ isRepairWorker ? '我的维修项目' : '维修项目监督' }}</strong>
              <span>{{ isRepairWorker ? '只显示分配给当前维修工的任务' : '管理员可分配维修工并查看节点进度' }}</span>
            </div>
            <el-tag type="warning">待处理 {{ pendingRepairCount }}</el-tag>
          </div>
          <el-table :data="repairs" stripe>
            <el-table-column label="工单号" prop="id" width="100" />
            <el-table-column label="房源" prop="property" min-width="160" />
            <el-table-column label="报修租客" prop="tenant" width="100" />
            <el-table-column label="问题描述" prop="desc" min-width="180" />
            <el-table-column label="报修时间" prop="date" width="110" />
            <el-table-column label="维修工" width="150">
              <template #default="{ row }">
                <el-select
                  v-if="canAssignRepair"
                  :model-value="row.assignee || ''"
                  size="small"
                  placeholder="未分配"
                  clearable
                  @change="(value: string) => assignRepair(row, value)"
                >
                  <el-option v-for="worker in repairWorkerOptions" :key="worker" :label="worker" :value="worker" />
                </el-select>
                <span v-else>{{ row.assignee || '未分配' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="节点进度" min-width="260">
              <template #default="{ row }">
                <div class="repair-steps">
                  <span
                    v-for="step in repairSteps(row)"
                    :key="step.key"
                    class="repair-step"
                    :class="{ done: step.done, active: step.active }"
                  >
                    <i>{{ step.done ? '✓' : '' }}</i>{{ step.label }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="最近提交" min-width="220">
              <template #default="{ row }">
                <div v-if="row.updateLogs?.length" class="repair-log-preview">
                  <strong>{{ row.updateLogs[0].status }}</strong>
                  <span>{{ row.updateLogs[0].reason }}</span>
                  <span>材料：{{ row.updateLogs[0].materials }}</span>
                  <span>图片 {{ row.updateLogs[0].images?.length || 0 }} 张</span>
                </div>
                <span v-else class="muted-text">暂无提交记录</span>
              </template>
            </el-table-column>
            <el-table-column label="当前状态" width="90">
              <template #default="{ row }">
                <el-tag :type="repairStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240">
              <template #default="{ row }">
                <el-button v-if="canAssignRepair" size="small" type="primary" @click="assignRepair(row, row.assignee || defaultRepairWorker)">派单</el-button>
                <el-button v-if="isRepairWorker" size="small" type="primary" @click="openRepairUpdate(row)">提交更新</el-button>
                <el-button v-if="isRepairWorker && row.status === '已派单'" size="small" @click="startRepair(row)">开始维修</el-button>
                <el-button v-if="canAssignRepair" size="small" type="success" @click="completeRepair(row)">完成</el-button>
                <el-button v-else-if="isRepairWorker" size="small" type="success" @click="openRepairComplete(row)">提交完成</el-button>
                <el-button size="small" text @click="uploadRepairProof(row)">凭证</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab7: 咨询&消息 -->
        <el-tab-pane v-if="canViewMessages" label="💬 消息中心" name="messages">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-card shadow="never" class="msg-card">
                <template #header><span>📩 租客咨询</span></template>
                <div v-for="m in messageRows" :key="m.id" class="msg-item">
                  <div class="msg-header">
                    <strong>{{ m.tenant }}</strong>
                    <span class="msg-time">{{ m.time }}</span>
                    <el-tag v-if="!m.read" type="danger" size="small">新</el-tag>
                  </div>
                  <p class="msg-text">{{ m.text }}</p>
                  <el-button size="small" text type="primary" @click="replyMessage(m)">回复</el-button>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="never" class="msg-card">
                <template #header><span>🔔 系统通知</span></template>
                <div v-for="n in noticeRows" :key="n.id" class="msg-item">
                  <span class="msg-time">{{ n.time }}</span>
                  <p class="msg-text">{{ n.text }}</p>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- Tab8: 账号权限 -->
        <el-tab-pane v-if="canViewAdminTabs" label="👤 账号权限" name="permissions">
          <el-row :gutter="16" class="permission-layout">
            <el-col :span="8" v-for="roleProfile in roleProfiles" :key="roleProfile.key">
              <el-card shadow="never" class="setting-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ roleProfile.name }}</span>
                    <el-tag :type="roleProfile.locked ? 'danger' : 'success'" size="small">
                      {{ roleProfile.locked ? '最高权限' : '可配置' }}
                    </el-tag>
                  </div>
                </template>
                <p class="role-desc">{{ roleProfile.desc }}</p>
                <el-checkbox-group v-model="roleProfile.permissions" class="permission-list" :disabled="roleProfile.locked">
                  <el-checkbox v-for="item in permissionCatalog" :key="item.key" :label="item.key">
                    {{ item.name }}
                  </el-checkbox>
                </el-checkbox-group>
                <el-button size="small" type="primary" :disabled="roleProfile.locked" @click="saveRoleProfile(roleProfile)">
                  保存角色模板
                </el-button>
              </el-card>
            </el-col>
          </el-row>
          <el-table :data="portalAccounts" stripe>
            <el-table-column label="账号" prop="name" width="150" />
            <el-table-column label="初始密码" prop="trialPassword" width="150" />
            <el-table-column label="角色" width="180">
              <template #default="{ row }">
                <el-select v-model="row.roleKey" :disabled="row.id === 'A-001'" @change="applyRoleTemplate(row)">
                  <el-option v-for="roleProfile in roleProfiles" :key="roleProfile.key" :label="roleProfile.name" :value="roleProfile.key" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="单项功能">
              <template #default="{ row }">
                <el-checkbox-group v-model="row.permissions" class="permission-list compact" :disabled="row.id === 'A-001'">
                  <el-checkbox v-for="item in permissionCatalog" :key="item.key" :label="item.key">
                    {{ item.name }}
                  </el-checkbox>
                </el-checkbox-group>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="saveAccount(row)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab9: 排班监督 -->
        <el-tab-pane v-if="canViewAdminTabs" label="📆 排班监督" name="schedules">
          <el-table :data="portalSchedules" stripe>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="name" label="人员" width="110" />
            <el-table-column prop="role" label="角色" width="140" />
            <el-table-column prop="city" label="城市" width="100" />
            <el-table-column prop="shift" label="班次" width="140" />
            <el-table-column prop="workOrders" label="工单数" width="100" />
            <el-table-column prop="conflict" label="冲突说明" min-width="180" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '冲突' ? 'danger' : 'success'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab10: 操作日志 -->
        <el-tab-pane v-if="canViewAdminTabs" label="🧾 操作日志" name="logs">
          <el-table :data="portalLogs" stripe>
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column prop="time" label="操作时间" width="180" />
            <el-table-column prop="type" label="类型" width="140" />
            <el-table-column prop="target" label="对象" width="140" />
            <el-table-column prop="content" label="内容" min-width="260" />
            <el-table-column prop="ip" label="IP" width="120" />
          </el-table>
        </el-tab-pane>

        <!-- Tab11: 门店设置 -->
        <el-tab-pane v-if="canViewAdminTabs" label="⚙️ 门店设置" name="settings">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-card shadow="never" class="setting-card">
                <template #header>🔐 账号安全</template>
                <el-form label-width="100px">
                  <el-form-item label="工作手机"><el-input v-model="adminPhone" /></el-form-item>
                  <el-form-item label="登录密码"><el-input type="password" model-value="********" /></el-form-item>
                  <el-form-item label="企业微信"><el-tag type="success">已绑定</el-tag> <el-button size="small" text type="warning">解绑</el-button></el-form-item>
                  <el-form-item><el-button type="primary" size="small">保存修改</el-button></el-form-item>
                </el-form>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="never" class="setting-card">
                <template #header>🏦 对公收款账户</template>
                <el-form label-width="100px">
                  <el-form-item label="开户银行"><el-input value="中国工商银行" /></el-form-item>
                  <el-form-item label="对公账号"><el-input value="6222 **** **** 8832" /></el-form-item>
                  <el-form-item label="账户名称"><el-input value="XX公寓管理有限公司" /></el-form-item>
                  <el-form-item><el-button type="primary" size="small">更新账户</el-button></el-form-item>
                </el-form>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="24" style="margin-top:16px">
            <el-col :span="12">
              <el-card shadow="never" class="setting-card">
                <template #header>📋 门店资质</template>
                <div class="qualification-list">
                  <div class="qual-item"><span>营业执照</span><el-tag type="success" size="small">已上传</el-tag><el-button size="small" text>查看</el-button></div>
                  <div class="qual-item"><span>产权合规材料</span><el-tag type="warning" size="small">待更新</el-tag><el-button size="small" text type="primary">上传</el-button></div>
                  <div class="qual-item"><span>运营人身份证</span><el-tag type="success" size="small">已认证</el-tag><el-button size="small" text>查看</el-button></div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="never" class="setting-card">
                <template #header>🔔 消息推送设置</template>
                <div class="notif-switches">
                  <el-switch v-model="pushSettings.sms" active-text="短信通知" />
                  <el-switch v-model="pushSettings.site" active-text="站内通知" />
                  <el-switch v-model="pushSettings.booking" active-text="新预约提醒" />
                  <el-switch v-model="pushSettings.rent" active-text="租金到账通知" />
                  <el-switch v-model="pushSettings.expire" active-text="合约到期预警" />
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 编辑资料弹窗 -->
    <el-dialog v-model="showEditProfile" title="编辑管理员资料" width="500px">
      <el-form label-width="100px">
        <el-form-item label="头像"><el-upload action="#" :auto-upload="false" :show-file-list="false"><el-button size="small" round>更换头像</el-button></el-upload></el-form-item>
        <el-form-item label="工作手机"><el-input v-model="adminPhone" /></el-form-item>
        <el-form-item label="收款账户"><el-input placeholder="对公银行账号" /></el-form-item>
        <el-form-item label="运营简介"><el-input type="textarea" :rows="3" placeholder="介绍您的公寓运营经验..." /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showEditProfile = false">取消</el-button><el-button type="primary" @click="showEditProfile = false">保存</el-button></template>
    </el-dialog>

    <!-- 资质上传弹窗 -->
    <el-dialog v-model="showUploadQualification" title="资质材料上传" width="500px">
      <el-form label-width="120px">
        <el-form-item label="营业执照"><el-upload action="#" :auto-upload="false"><el-button type="primary" size="small">选择文件</el-button></el-upload></el-form-item>
        <el-form-item label="产权合规材料"><el-upload action="#" :auto-upload="false"><el-button type="primary" size="small">选择文件</el-button></el-upload></el-form-item>
        <el-form-item label="身份证核验"><el-upload action="#" :auto-upload="false"><el-button type="primary" size="small">选择文件</el-button></el-upload></el-form-item>
      </el-form>
      <template #footer><el-button @click="showUploadQualification = false">取消</el-button><el-button type="primary" @click="submitQualification">提交审核</el-button></template>
    </el-dialog>

    <el-dialog v-model="repairUpdateVisible" title="提交维修进度" width="560px">
      <el-form label-position="top">
        <el-form-item label="维修项目">
          <el-input :model-value="activeRepair?.id ? `${activeRepair.id}｜${activeRepair.property}` : ''" disabled />
        </el-form-item>
        <el-form-item label="当前节点">
          <el-select v-model="repairUpdateForm.status" style="width:100%">
            <el-option label="已派单" value="已派单" />
            <el-option label="维修中" value="维修中" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>
        <el-form-item label="维修原因">
          <el-input v-model="repairUpdateForm.reason" type="textarea" :rows="3" placeholder="说明故障原因、现场判断或无法维修的原因" />
        </el-form-item>
        <el-form-item label="使用材料">
          <el-input v-model="repairUpdateForm.materials" type="textarea" :rows="3" placeholder="填写更换或使用的材料，例如水管接头、密封胶、空调滤芯" />
        </el-form-item>
        <el-form-item label="现场图片">
          <el-upload
            v-model:file-list="repairUpdateFiles"
            list-type="picture-card"
            :auto-upload="false"
            :limit="5"
            accept="image/*"
          >
            <span>上传</span>
          </el-upload>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input v-model="repairUpdateForm.result" type="textarea" :rows="3" placeholder="填写本次维修进展、下一步安排或完成结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="repairUpdateVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRepairUpdate">提交更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadUserFile } from 'element-plus'
import { repairService, type Repair } from '@/services/repair'
import { bookingService } from '@/services/booking'
import type { Booking, Notification } from '@/types/booking'
import { useAuthStore } from '@/stores/auth'
import { adminPortalService } from '@/services/adminPortal'
import { propertyService } from '@/services/property'
import { adminService } from '@/services/admin'
import type { Property, PropertyStatus } from '@/types/property'
import type { User } from '@/types/user'

type PropertyManagerOption = Pick<User, 'id' | 'username'>
import { notificationService } from '@/services/notification'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const role = computed(() => authStore.user?.role || 'tenant')
const isAdmin = computed(() => role.value === 'admin')
const roleLabel = computed(() => {
  const labels: Record<string, string> = {
    admin: '超级管理员',
    appointment_staff: '预约对接人员',
    property_manager: '房源管理人员',
    repair_worker: '维修工',
    landlord: '公寓运营商',
  }
  return labels[role.value] || '运营人员'
})
const roleTagType = computed(() => {
  if (role.value === 'admin') return 'danger'
  if (role.value === 'appointment_staff') return 'success'
  if (role.value === 'property_manager') return 'warning'
  if (role.value === 'repair_worker') return 'info'
  return 'info'
})
const isRepairWorker = computed(() => role.value === 'repair_worker')
const canViewProperties = computed(() => ['admin', 'landlord', 'property_manager'].includes(role.value))
const canViewBookings = computed(() => ['admin', 'landlord', 'appointment_staff'].includes(role.value))
const canViewRepairs = computed(() => ['admin', 'landlord', 'appointment_staff', 'repair_worker'].includes(role.value))
const canViewMessages = computed(() => ['admin', 'landlord', 'appointment_staff'].includes(role.value))
const canAssignRepair = computed(() => ['admin', 'landlord', 'appointment_staff'].includes(role.value))
const canViewAdminTabs = computed(() => isAdmin.value)
const availableTabs = computed(() => {
  const tabs: string[] = []
  if (canViewProperties.value) tabs.push('properties')
  if (canViewBookings.value) tabs.push('bookings')
  if (canViewAdminTabs.value) tabs.push('contracts', 'finance', 'tenants', 'permissions', 'schedules', 'logs', 'settings')
  if (canViewRepairs.value) tabs.push('repairs')
  if (canViewMessages.value) tabs.push('messages')
  return tabs
})

function canOpenTab(tab: string) {
  return availableTabs.value.includes(tab)
}

// ── 管理员信息 ──
const adminName = ref('张经理')
const adminEmail = ref('zhang@rental.com')
const adminPhone = ref('139****5678')
const adminDistrict = ref('朝阳区·海淀区')
const adminSince = ref('2025-03-15')
const verified = ref(true)

const showEditProfile = ref(false)
const showUploadQualification = ref(false)
const repairUpdateVisible = ref(false)
const activeRepair = ref<Repair | null>(null)
const repairUpdateFiles = ref<UploadUserFile[]>([])
const repairUpdateForm = reactive({
  status: '维修中',
  reason: '',
  materials: '',
  result: '',
})

// ── 统计卡片 ──
const repairs = ref<Repair[]>([])
const bookings = ref<Booking[]>([])
const properties = ref<Property[]>([])
const propertyManagers = ref<User[]>([])
const notifications = ref<Notification[]>([])
const portalMessages = ref<any[]>([])
const portalAccounts = ref<any[]>([])
const roleProfiles = ref<any[]>([])
const permissionCatalog = ref<any[]>([])
const portalSchedules = ref<any[]>([])
const portalLogs = ref<any[]>([])
const portalFinanceItems = ref<any[]>([])
const pendingRepairCount = computed(() => repairs.value.filter((item) => item.status !== '已完成').length)
const repairWorkerOptions = computed(() => {
  const workers = portalAccounts.value
    .filter((account) => account.roleKey === 'repair_worker' || account.role === '维修工')
    .map((account) => account.login || account.name)
    .filter(Boolean)
  return workers.length ? workers : ['repair_worker']
})
const defaultRepairWorker = computed(() => repairWorkerOptions.value[0] || 'repair_worker')
const propertyManagerOptions = computed<PropertyManagerOption[]>(() => {
  if (propertyManagers.value.length) return propertyManagers.value
  return portalAccounts.value
    .filter((account) => account.roleKey === 'property_manager')
    .map((account, index) => ({
      id: Number(account.userId || account.numericId || index + 1),
      username: account.login || account.name,
    }))
})
const financePendingCount = computed(() => portalFinanceItems.value.filter((item) => !['已退款', '已扣款', '已完结'].includes(item.status)).length)
const financeTotal = computed(() => portalFinanceItems.value.reduce((total, item) => {
  const amount = Number(String(item.amount || '').replace(/[^\d.-]/g, ''))
  return Number.isFinite(amount) ? total + amount : total
}, 0))

const statsCards = computed(() =>
  [
    { icon: '🏠', label: '管理房源', value: propertyRows.value.length, sub: `空置${vacantCount.value} · 已租${rentedCount.value}`, tab: 'properties' },
    { icon: '📅', label: '待处理预约', value: pendingBookingCount.value, sub: `全部预约 ${bookings.value.length} 单`, tab: 'bookings' },
    { icon: '💰', label: '财务待处理', value: financePendingCount.value, sub: `登记金额 ${financeTotal.value}`, tab: 'finance' },
    { icon: '📄', label: '合同统计', value: contractRows.value.length, sub: `生效中 ${activeContractCount.value} 份`, tab: 'contracts' },
    { icon: '🔧', label: '待处理工单', value: pendingRepairCount.value, sub: `报修 ${pendingRepairCount.value} 条`, tab: 'repairs' },
    { icon: '👁️', label: '消息通知', value: messageRows.value.length + noticeRows.value.length, sub: `未读 ${messageRows.value.filter((item) => !item.read).length + noticeRows.value.filter((item) => !item.read).length} 条`, tab: 'messages' },
  ].filter((item) => canOpenTab(item.tab)),
)

// ── Tab 状态 ──
const activeTab = ref((route.query.tab as string) || 'properties')
const propertyFilter = ref('all')
const bookingFilter = ref('all')
const contractFilter = ref('active')
const financeTab = ref('deposit')
const pushSettings = reactive({ sms: true, site: true, booking: true, rent: true, expire: true })

function ensureAllowedTab() {
  if (!availableTabs.value.includes(activeTab.value)) {
    activeTab.value = availableTabs.value[0] || 'properties'
  }
}

watch(availableTabs, ensureAllowedTab, { immediate: true })
watch(() => route.query.tab, (tab) => {
  if (typeof tab === 'string' && availableTabs.value.includes(tab)) {
    activeTab.value = tab
  }
})

// ── 辅助函数 ──
const statusTag = (s: string) => ({ '空置': 'info', '已出租': 'success', '维护中': 'warning', '待上架': 'danger' }[s] || 'info') as 'info'|'success'|'warning'|'danger'
const bookingStatusTag = (s: string) => ({ 'pending': 'warning', 'approved': 'success', 'rejected': 'danger', 'cancelled': 'info', 'completed': 'success' }[s] || 'info') as 'warning'|'success'|'danger'|'info'
const repairStatusTag = (s: string) => ({ '待处理': 'danger', '已派单': 'warning', '维修中': '', '已完成': 'success' }[s] || 'info') as 'danger'|'warning'|''|'success'|'info'
const repairStepLabels = ['待处理', '已派单', '维修中', '已完成']
function repairSteps(row: Repair) {
  if (row.progressSteps?.length) return row.progressSteps
  const activeIndex = Math.max(0, repairStepLabels.indexOf(row.status))
  return repairStepLabels.map((label, index) => ({
    key: label,
    label,
    done: index <= activeIndex,
    active: index === activeIndex,
  }))
}

const propertyStatusLabels: Record<PropertyStatus, string> = {
  available: '空置',
  rented: '已出租',
  maintenance: '维护中',
  offline: '待上架',
}
const propertyStatusValues: Record<string, PropertyStatus> = {
  空置: 'available',
  已出租: 'rented',
  维护中: 'maintenance',
  待上架: 'offline',
}
const propertyRows = computed(() => properties.value.map((property) => ({
  id: property.id,
  address: property.address || property.title,
  bedrooms: property.bedrooms,
  bathrooms: property.bathrooms,
  price: property.price_monthly,
  status: propertyStatusLabels[property.status] || property.status,
  propertyManagerId: property.property_manager_id || null,
  propertyManagerName: property.property_manager_id
    ? propertyManagerOptions.value.find((manager) => manager.id === property.property_manager_id)?.username || `负责人 #${property.property_manager_id}`
    : '未分配',
  tenant: property.status === 'rented' ? '已出租' : '—',
  raw: property,
})))
const vacantCount = computed(() => propertyRows.value.filter(p => p.status === '空置').length)
const rentedCount = computed(() => propertyRows.value.filter(p => p.status === '已出租').length)
const filteredProperties = computed(() => {
  if (propertyFilter.value === 'all') return propertyRows.value
  const map: Record<string, string> = { vacant: '空置', rented: '已出租', maintenance: '维护中', pending: '待上架' }
  return propertyRows.value.filter(p => p.status === map[propertyFilter.value])
})

// ── 派生业务数据 ──
const bookingStatusText = (s: string) => ({ pending: '待处理', approved: '已同意', rejected: '已拒绝', cancelled: '已取消', completed: '已完成' }[s] || s)
const bookingRows = computed(() => bookings.value.map((booking) => ({
  id: booking.id,
  property: `房源 #${booking.property_id}`,
  tenant: `租客 #${booking.tenant_id}`,
  phone: '已脱敏',
  date: booking.scheduled_date || new Date(booking.created_at).toLocaleDateString('zh-CN'),
  status: booking.status,
  statusText: bookingStatusText(booking.status),
  message: booking.message || '',
  raw: booking,
})))
const pendingBookingCount = computed(() => bookings.value.filter(b => b.status === 'pending').length)
const filteredBookings = computed(() => {
  if (bookingFilter.value === 'all') return bookingRows.value
  return bookingRows.value.filter(b => b.status === bookingFilter.value)
})

const contractRows = computed(() => bookingRows.value.map((booking) => {
  const property = properties.value.find((item) => item.id === booking.raw.property_id)
  const createdAt = new Date(booking.raw.created_at)
  const endAt = new Date(createdAt)
  endAt.setFullYear(endAt.getFullYear() + 1)
  const isActive = ['approved', 'completed'].includes(booking.raw.status)
  return {
    id: `HT-${booking.id}`,
    property: property?.title || booking.property,
    tenant: booking.tenant,
    startDate: isActive ? createdAt.toLocaleDateString('zh-CN') : '—',
    endDate: isActive ? endAt.toLocaleDateString('zh-CN') : '—',
    rent: property ? `¥${property.price_monthly}` : '待确认',
    deposit: booking.raw.deposit_amount ? `¥${booking.raw.deposit_amount}` : '待确认',
    status: booking.raw.status === 'approved' || booking.raw.status === 'completed' ? '生效中' : '待签约定金',
  }
}))
const activeContractCount = computed(() => contractRows.value.filter(c => c.status === '生效中').length)
const filteredContracts = computed(() => {
  if (contractFilter.value === 'active') return contractRows.value.filter(c => c.status === '生效中')
  if (contractFilter.value === 'expiring') return contractRows.value.filter(c => c.status === '即将到期')
  if (contractFilter.value === 'deposit') return contractRows.value.filter(c => c.status === '待签约定金')
  return contractRows.value
})

const financeData = computed(() => portalFinanceItems.value.map((item) => ({
  id: item.id,
  type: item.type,
  property: item.property,
  tenant: item.customer,
  amount: item.amount,
  date: item.createdAt ? new Date(item.createdAt).toLocaleDateString('zh-CN') : '待记录',
  status: item.status,
})))

const tenantRows = computed(() => contractRows.value
  .filter((contract) => contract.status === '生效中')
  .map((contract) => ({
    name: contract.tenant,
    phone: '已脱敏',
    property: contract.property,
    contractId: contract.id,
    rent: contract.rent,
    payStatus: '正常',
    endDate: contract.endDate,
  })))

const messageRows = computed(() => portalMessages.value.map((message) => ({
  id: message.id,
  tenant: message.sender,
  time: message.createdAt ? new Date(message.createdAt).toLocaleString('zh-CN') : '',
  text: message.summary,
  read: message.status === '已读',
  related: message.related,
})))

const noticeRows = computed(() => notifications.value.map((notice) => ({
  id: notice.id,
  time: new Date(notice.created_at).toLocaleString('zh-CN'),
  text: `${notice.title}${notice.content ? `：${notice.content}` : ''}`,
  read: notice.is_read,
})))

// ── 操作函数 ──
async function recordWorkspaceAction(action: string, target: string, content: string) {
  await adminPortalService.recordAction({ action, target, content })
}

function editProperty(row: any) {
  router.push(`/property/${row.id}/edit`)
}

async function updatePropertyStatus(row: any, status: PropertyStatus, successText: string) {
  await propertyService.update(row.id, { status })
  await recordWorkspaceAction('property.status', `property-${row.id}`, `${row.address}：${successText}`)
  ElMessage.success(successText)
  await fetchProperties()
}

async function assignPropertyManager(row: any, value: number | string) {
  const propertyManagerId = value ? Number(value) : null
  await propertyService.update(row.id, { property_manager_id: propertyManagerId })
  const managerName = propertyManagerId
    ? propertyManagerOptions.value.find((manager) => manager.id === propertyManagerId)?.username || `负责人 #${propertyManagerId}`
    : '未分配'
  await recordWorkspaceAction('property.manager.assign', `property-${row.id}`, `${row.address}：负责人调整为 ${managerName}`)
  ElMessage.success(`房源负责人已调整为 ${managerName}`)
  await fetchProperties()
}

async function maintainProperty(row: any) {
  await updatePropertyStatus(row, 'maintenance', '房源已标记为维护中')
}

function viewPropertyBookings(row: any) {
  activeTab.value = 'bookings'
  ElMessage.success(`已切换到预约管理，可查看房源 ${row.id} 的预约`)
}

function handleBatchAdd() {
  router.push('/property/create')
}

async function handleBatchPublish() {
  await Promise.all(filteredProperties.value.map((row: any) => propertyService.update(row.id, { status: 'available' })))
  await recordWorkspaceAction('property.batch_publish', 'properties', `批量上架 ${filteredProperties.value.length} 套房源`)
  ElMessage.success('当前筛选房源已批量上架')
  await fetchProperties()
}

async function handleBatchOffline() {
  await Promise.all(filteredProperties.value.map((row: any) => propertyService.update(row.id, { status: 'offline' })))
  await recordWorkspaceAction('property.batch_offline', 'properties', `批量下架 ${filteredProperties.value.length} 套房源`)
  ElMessage.success('当前筛选房源已批量下架')
  await fetchProperties()
}

async function approveBooking(row: any) {
  await bookingService.updateStatus(row.id, 'approved')
  ElMessage.success(`已确认 ${row.tenant} 的看房预约`)
  await fetchBookings()
}

async function rejectBooking(row: any) {
  await bookingService.updateStatus(row.id, 'rejected')
  ElMessage.info(`已驳回 ${row.tenant} 的看房预约`)
  await fetchBookings()
}
async function handleBatchRemind() {
  await recordWorkspaceAction('booking.remind', 'bookings', `批量发送 ${filteredBookings.value.length} 条看房提醒`)
  ElMessage.success('看房提醒已写入消息/日志')
}
async function viewTenantInfo(row: any) {
  await recordWorkspaceAction('booking.tenant_view', `booking-${row.id}`, row.message || `查看租客信息: ${row.tenant}`)
  ElMessage.success('租客信息查看动作已写入日志')
}
async function markVisited(row: any) {
  await bookingService.updateStatus(row.id, 'completed')
  await recordWorkspaceAction('booking.visited', `booking-${row.id}`, `${row.tenant} 已接待并完成带看`)
  ElMessage.success(`已标记 ${row.tenant} 为已接待`)
  await fetchBookings()
}

async function batchGenerateContracts() {
  await recordWorkspaceAction('contract.generate', 'contracts', `批量生成 ${filteredContracts.value.length} 份电子合同`)
  ElMessage.success('合同生成任务已写入工作日志')
}
async function batchExportContracts() {
  await recordWorkspaceAction('contract.export', 'contracts', `批量导出 ${filteredContracts.value.length} 份合同`)
  ElMessage.success('合同导出任务已写入工作日志')
}
async function batchRenewContracts() {
  await recordWorkspaceAction('contract.renew', 'contracts', `批量发起 ${filteredContracts.value.length} 份续租`)
  ElMessage.success('续租任务已写入工作日志')
}
function viewContract(row: any) { router.push(`/contract/${row.id}`) }
function terminateContract(row: any) {
  ElMessageBox.confirm(`确定解除合同 ${row.id}？`, '确认解约', { type: 'warning' })
    .then(async () => {
      row.status = '已解约'
      await recordWorkspaceAction('contract.terminate', row.id, `发起解约：${row.id}`)
      ElMessage.success('已发起解约')
    })
}

async function viewTenantDetail(row: any) {
  await recordWorkspaceAction('tenant.detail', row.name, `查看租客详情：${row.name}`)
  ElMessage.success(`已记录租客查看动作：${row.name}`)
}
async function viewTenantPayments(row: any) {
  await recordWorkspaceAction('tenant.payments', row.name, `查看缴费记录：${row.name}`)
  ElMessage.success(`已记录缴费查询：${row.name}`)
}
async function viewTenantRepairs(row: any) {
  activeTab.value = 'repairs'
  await recordWorkspaceAction('tenant.repairs', row.name, `查看报修历史：${row.name}`)
}

async function fetchRepairs() {
  try { repairs.value = await repairService.list() }
  catch { repairs.value = [] }
}

async function fetchBookings() {
  try { bookings.value = await bookingService.list() }
  catch { bookings.value = [] }
}

async function fetchProperties() {
  if (!canViewProperties.value) return
  const params: { limit: number; property_manager_id?: number } = { limit: 100 }
  if (role.value === 'property_manager' && authStore.user?.id) {
    params.property_manager_id = authStore.user.id
  }
  try { properties.value = await propertyService.list(params) }
  catch { properties.value = [] }
}

async function fetchPropertyManagers() {
  if (role.value === 'property_manager' && authStore.user) {
    propertyManagers.value = [authStore.user]
    return
  }
  if (!isAdmin.value) return
  try {
    propertyManagers.value = await adminService.listUsers({ role: 'property_manager', limit: 100 })
  } catch {
    propertyManagers.value = []
  }
}

async function fetchNotifications() {
  if (!canViewMessages.value) return
  try { notifications.value = await notificationService.list() }
  catch { notifications.value = [] }
}

async function fetchPortalState() {
  if (!isAdmin.value) return
  try {
    const state = await adminPortalService.getState()
    portalAccounts.value = state.accounts || []
    roleProfiles.value = state.roleProfiles || []
    permissionCatalog.value = state.permissionCatalog || []
    portalSchedules.value = state.schedules || []
    portalLogs.value = state.logs || []
    portalMessages.value = state.messages || []
    portalFinanceItems.value = state.financeItems || []
  } catch {
    portalAccounts.value = []
    roleProfiles.value = []
    permissionCatalog.value = []
    portalSchedules.value = []
    portalLogs.value = []
    portalMessages.value = []
    portalFinanceItems.value = []
  }
}

function applyRoleTemplate(row: any) {
  const roleProfile = roleProfiles.value.find((item) => item.key === row.roleKey)
  if (!roleProfile || row.id === 'A-001') return
  row.role = roleProfile.name
  row.permissions = [...roleProfile.permissions]
}

async function saveRoleProfile(roleProfile: any) {
  await adminPortalService.updateRoleProfile(roleProfile.key, { permissions: roleProfile.permissions })
  ElMessage.success('角色模板已保存')
  await fetchPortalState()
}

async function saveAccount(row: any) {
  await adminPortalService.updateAccount(row.id, {
    roleKey: row.roleKey,
    permissions: row.permissions,
    status: row.status,
  })
  ElMessage.success('账号权限已保存')
  await fetchPortalState()
}

async function submitQualification() {
  await recordWorkspaceAction('qualification.submit', authStore.user?.username || 'workspace', '提交资质材料审核')
  showUploadQualification.value = false
  ElMessage.success('资质材料已提交审核并写入日志')
}

async function assignRepair(row: Repair, assignee?: string) {
  const worker = assignee || defaultRepairWorker.value
  if (!worker) {
    ElMessage.error('请先选择维修工')
    return
  }
  await repairService.update(row.id, { status: '已派单', assignee: worker, result: `已分配给维修工 ${worker}` })
  ElMessage.success(`工单 ${row.id} 已分配给 ${worker}`)
  await fetchRepairs()
}

async function startRepair(row: Repair) {
  await repairService.update(row.id, { status: '维修中', result: `${authStore.user?.username || '维修工'} 已开始维修` })
  ElMessage.success(`工单 ${row.id} 已进入维修中`)
  await fetchRepairs()
}
async function completeRepair(row: Repair) {
  await repairService.update(row.id, { status: '已完成', result: `${authStore.user?.username || '维修工'} 已完成维修` })
  ElMessage.success(`工单 ${row.id} 已标记完成`)
  await fetchRepairs()
}

function openRepairUpdate(row: Repair) {
  activeRepair.value = row
  repairUpdateForm.status = row.status === '已完成' ? '已完成' : row.status === '已派单' ? '维修中' : row.status
  repairUpdateForm.reason = row.reason || ''
  repairUpdateForm.materials = row.materials || ''
  repairUpdateForm.result = row.result || ''
  repairUpdateFiles.value = []
  repairUpdateVisible.value = true
}

function openRepairComplete(row: Repair) {
  openRepairUpdate(row)
  repairUpdateForm.status = '已完成'
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

async function submitRepairUpdate() {
  if (!activeRepair.value) return
  if (!repairUpdateForm.reason.trim()) {
    ElMessage.error('请填写维修原因')
    return
  }
  if (!repairUpdateForm.materials.trim()) {
    ElMessage.error('请填写使用材料')
    return
  }
  if (!repairUpdateForm.result.trim()) {
    ElMessage.error('请填写处理说明')
    return
  }
  const rawFiles = repairUpdateFiles.value
    .map((item) => item.raw)
    .filter((file): file is File => file instanceof File)
  if (rawFiles.length === 0) {
    ElMessage.error('请至少上传一张现场图片')
    return
  }

  const evidenceImages = await Promise.all(rawFiles.map(async (file) => ({
    name: file.name,
    size: file.size,
    dataUrl: await fileToDataUrl(file),
  })))

  await repairService.update(activeRepair.value.id, {
    status: repairUpdateForm.status,
    reason: repairUpdateForm.reason.trim(),
    materials: repairUpdateForm.materials.trim(),
    result: repairUpdateForm.result.trim(),
    evidenceImages,
  })
  repairUpdateVisible.value = false
  ElMessage.success('维修进度已提交')
  await fetchRepairs()
}

async function uploadRepairProof(row: any) {
  await recordWorkspaceAction('repair.proof', String(row.id), `已登记维修凭证入口：${row.id}`)
  ElMessage.success(`维修凭证登记已写入日志：${row.id}`)
}

async function replyMessage(m: any) {
  await recordWorkspaceAction('message.reply', String(m.id), `回复 ${m.tenant} 的消息：${m.text}`)
  ElMessage.success('回复动作已写入消息日志')
  await fetchPortalState()
}

onMounted(async () => {
  ensureAllowedTab()
  await Promise.all([fetchPropertyManagers(), fetchPortalState()])
  await Promise.all([fetchBookings(), fetchRepairs(), fetchProperties(), fetchNotifications()])
})
</script>

<style scoped>
.workspace-page { max-width: 1200px; margin: 0 auto; }

/* ── User Card ── */
.user-card { margin-bottom: 20px; }
.user-info { display: flex; align-items: center; gap: 20px; }
.user-detail { flex: 1; }
.user-name-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.user-name { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.user-contact { display: flex; gap: 20px; font-size: 13px; color: var(--text-muted); flex-wrap: wrap; }
.user-actions { display: flex; gap: 10px; flex-shrink: 0; }

/* ── Stats Grid ── */
.stats-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: var(--bg-white); border-radius: var(--radius); border: 1px solid var(--border); padding: 14px 12px; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: all 0.2s; min-height: 70px; }
.stat-card:hover { border-color: var(--primary); box-shadow: var(--shadow); transform: translateY(-2px); }
.stat-icon { font-size: 24px; }
.stat-num { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-muted); }
.stat-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* ── Tabs ── */
.tabs-card { border-radius: var(--radius) !important; }
.workspace-tabs :deep(.el-tabs__item) { font-size: 14px; font-weight: 500; }
.tab-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }

/* ── Finance ── */
.finance-summary { margin-bottom: 16px; }

/* ── Messages ── */
.msg-card { height: 400px; overflow-y: auto; }
.msg-item { padding: 10px 0; border-bottom: 1px solid var(--border-light); }
.msg-item:last-child { border-bottom: none; }
.msg-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.msg-time { font-size: 12px; color: var(--text-muted); margin-left: auto; }
.msg-text { font-size: 13px; color: var(--text-secondary); margin: 4px 0; }

.repair-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  background: var(--bg);
}

.repair-summary strong,
.repair-summary span {
  display: block;
}

.repair-summary span {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 13px;
}

.repair-steps {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.repair-step {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text-muted);
  font-size: 12px;
}

.repair-step::after {
  content: '';
  width: 18px;
  height: 1px;
  background: var(--border);
  margin-left: 2px;
}

.repair-step:last-child::after {
  display: none;
}

.repair-step i {
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

.repair-step.done {
  color: var(--text-primary);
}

.repair-step.done i {
  border-color: var(--primary);
  background: var(--primary);
  color: #fff;
}

.repair-step.active {
  font-weight: 700;
}

.repair-log-preview {
  display: grid;
  gap: 3px;
  font-size: 12px;
  line-height: 1.35;
}

.repair-log-preview strong {
  color: var(--text-primary);
}

.repair-log-preview span,
.muted-text {
  color: var(--text-muted);
}

/* ── Settings ── */
.setting-card { margin-bottom: 16px; }
.card-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.role-desc { margin: 0 0 10px; color: var(--text-muted); font-size: 13px; line-height: 1.5; }
.permission-layout { margin-bottom: 16px; }
.permission-list { display: grid; grid-template-columns: 1fr; gap: 6px; margin-bottom: 12px; }
.permission-list.compact { grid-template-columns: repeat(3, minmax(150px, 1fr)); margin-bottom: 0; }
.qualification-list { display: flex; flex-direction: column; gap: 12px; }
.qual-item { display: flex; align-items: center; gap: 12px; font-size: 14px; }
.notif-switches { display: flex; flex-direction: column; gap: 12px; }
</style>
