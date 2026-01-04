<template>
  <div class="report-push">
    <!-- 推送设置卡片 -->
    <el-card class="setting-card">
      <template #header>
        <div class="card-header">
          <span>推送设置</span>
        </div>
      </template>

      <el-form :model="pushSettings" label-width="120px">
        <el-form-item label="定时推送">
          <el-switch v-model="pushSettings.enabled" />
          <span class="setting-desc">启用后每天按设定时间自动推送</span>
        </el-form-item>

        <el-form-item label="推送时间" v-if="pushSettings.enabled">
          <el-time-picker
            v-model="pushSettings.pushTime"
            format="HH:mm"
            placeholder="选择推送时间"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 推送人员管理 -->
    <el-card class="recipients-card">
      <template #header>
        <div class="card-header">
          <span>推送人员</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加人员
          </el-button>
        </div>
      </template>

      <el-table :data="recipients" v-loading="loadingRecipients" empty-text="暂无推送人员">
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="添加时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              size="small"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              text
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 手动推送 -->
    <el-card class="manual-push-card">
      <template #header>
        <div class="card-header">
          <span>手动推送</span>
        </div>
      </template>

      <el-form :model="manualPush" label-width="120px">
        <el-form-item label="报表类型">
          <el-checkbox-group v-model="manualPush.reportTypes">
            <el-checkbox label="overview">数据概览</el-checkbox>
            <el-checkbox label="tools">工具排行</el-checkbox>
            <el-checkbox label="users">用户统计</el-checkbox>
            <el-checkbox label="trend">使用趋势</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="统计周期">
          <el-radio-group v-model="manualPush.days">
            <el-radio :label="1">今天</el-radio>
            <el-radio :label="7">近7天</el-radio>
            <el-radio :label="30">近30天</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="推送方式">
          <el-radio-group v-model="manualPush.method">
            <el-radio label="feishu">飞书消息</el-radio>
            <el-radio label="email">邮件(Excel附件)</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handlePush" :loading="pushing">
            <el-icon><Promotion /></el-icon>
            立即推送
          </el-button>
          <el-button @click="handlePreview">
            <el-icon><View /></el-icon>
            预览报表
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 推送历史 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>推送历史</span>
        </div>
      </template>

      <el-table :data="pushHistory" v-loading="loadingHistory" empty-text="暂无推送记录">
        <el-table-column label="推送时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.pushed_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="report_type" label="报表类型" width="120" />
        <el-table-column prop="push_method" label="推送方式" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.push_method === 'feishu' ? 'primary' : 'success'">
              {{ row.push_method === 'feishu' ? '飞书' : '邮件' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="recipient_count" label="接收人数" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_msg" label="备注" min-width="200" show-overflow-tooltip />
      </el-table>

      <div class="pagination-wrap" v-if="historyTotal > 10">
        <el-pagination
          v-model:current-page="historyPage"
          :page-size="10"
          :total="historyTotal"
          layout="prev, pager, next"
          @current-change="loadHistory"
        />
      </div>
    </el-card>

    <!-- 添加人员弹窗 -->
    <el-dialog v-model="showAddDialog" title="添加推送人员" width="480px">
      <el-form :model="newRecipient" :rules="recipientRules" ref="recipientFormRef" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="newRecipient.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="newRecipient.email" placeholder="请输入飞书邮箱" />
          <div class="form-tip">请填写飞书关联的邮箱地址</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddRecipient" :loading="addingRecipient">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog v-model="showPreviewDialog" title="报表预览" width="800px">
      <div class="preview-content" v-loading="loadingPreview">
        <div v-if="previewData">
          <!-- 概览 -->
          <div class="preview-section" v-if="previewData.overview">
            <h4>数据概览</h4>
            <div class="overview-grid">
              <div class="overview-item">
                <span class="label">总PV</span>
                <span class="value">{{ previewData.overview.total_pv }}</span>
              </div>
              <div class="overview-item">
                <span class="label">总UV</span>
                <span class="value">{{ previewData.overview.total_uv }}</span>
              </div>
              <div class="overview-item">
                <span class="label">今日PV</span>
                <span class="value">{{ previewData.overview.today_pv }}</span>
              </div>
              <div class="overview-item">
                <span class="label">今日UV</span>
                <span class="value">{{ previewData.overview.today_uv }}</span>
              </div>
            </div>
          </div>

          <!-- 工具排行 -->
          <div class="preview-section" v-if="previewData.tools?.length">
            <h4>工具排行 TOP10</h4>
            <el-table :data="previewData.tools" size="small">
              <el-table-column type="index" label="排名" width="60" />
              <el-table-column prop="name" label="工具名称" />
              <el-table-column prop="click_count" label="点击次数" width="100" />
            </el-table>
          </div>

          <!-- 用户统计 -->
          <div class="preview-section" v-if="previewData.users?.length">
            <h4>活跃用户 TOP10</h4>
            <el-table :data="previewData.users" size="small">
              <el-table-column type="index" label="排名" width="60" />
              <el-table-column prop="name" label="用户名" />
              <el-table-column prop="click_count" label="访问次数" width="100" />
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPreviewDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Promotion, View } from '@element-plus/icons-vue'
import { adminApi } from '@/api'

// 推送设置
const pushSettings = reactive({
  enabled: false,
  pushTime: null
})
const saving = ref(false)

// 推送人员
const recipients = ref([])
const loadingRecipients = ref(false)
const showAddDialog = ref(false)
const addingRecipient = ref(false)
const newRecipient = reactive({
  name: '',
  email: ''
})
const recipientFormRef = ref(null)
const recipientRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 手动推送
const manualPush = reactive({
  reportTypes: ['overview', 'tools'],
  days: 7,
  method: 'feishu'
})
const pushing = ref(false)

// 推送历史
const pushHistory = ref([])
const loadingHistory = ref(false)
const historyPage = ref(1)
const historyTotal = ref(0)

// 预览
const showPreviewDialog = ref(false)
const loadingPreview = ref(false)
const previewData = ref(null)

onMounted(() => {
  loadSettings()
  loadRecipients()
  loadHistory()
})

// 加载设置
async function loadSettings() {
  try {
    const data = await adminApi.getReportPushSettings()
    pushSettings.enabled = data.enabled
    if (data.push_time) {
      const [hour, minute] = data.push_time.split(':')
      pushSettings.pushTime = new Date()
      pushSettings.pushTime.setHours(parseInt(hour), parseInt(minute), 0)
    }
  } catch (e) {
    console.error('加载设置失败:', e)
  }
}

// 保存设置
async function saveSettings() {
  saving.value = true
  try {
    let pushTime = null
    if (pushSettings.pushTime) {
      const d = new Date(pushSettings.pushTime)
      pushTime = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    }
    await adminApi.saveReportPushSettings({
      enabled: pushSettings.enabled,
      push_time: pushTime
    })
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 加载推送人员
async function loadRecipients() {
  loadingRecipients.value = true
  try {
    recipients.value = await adminApi.getReportRecipients()
  } catch (e) {
    console.error('加载推送人员失败:', e)
  } finally {
    loadingRecipients.value = false
  }
}

// 添加推送人员
async function handleAddRecipient() {
  const valid = await recipientFormRef.value?.validate().catch(() => false)
  if (!valid) return

  addingRecipient.value = true
  try {
    await adminApi.addReportRecipient(newRecipient)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    newRecipient.name = ''
    newRecipient.email = ''
    loadRecipients()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    addingRecipient.value = false
  }
}

// 切换状态
async function toggleStatus(row) {
  try {
    await adminApi.updateReportRecipient(row.id, { is_active: !row.is_active })
    row.is_active = !row.is_active
    ElMessage.success('状态已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

// 删除人员
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除 ${row.name} 吗？`, '提示', {
      type: 'warning'
    })
    await adminApi.deleteReportRecipient(row.id)
    ElMessage.success('删除成功')
    loadRecipients()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 加载推送历史
async function loadHistory() {
  loadingHistory.value = true
  try {
    const res = await adminApi.getReportPushHistory(historyPage.value, 10)
    pushHistory.value = res.items
    historyTotal.value = res.total
  } catch (e) {
    console.error('加载推送历史失败:', e)
  } finally {
    loadingHistory.value = false
  }
}

// 手动推送
async function handlePush() {
  if (manualPush.reportTypes.length === 0) {
    ElMessage.warning('请选择报表类型')
    return
  }

  if (recipients.value.filter(r => r.is_active).length === 0) {
    ElMessage.warning('请先添加推送人员')
    return
  }

  pushing.value = true
  try {
    await adminApi.pushReport({
      report_types: manualPush.reportTypes,
      days: manualPush.days,
      method: manualPush.method
    })
    ElMessage.success('推送成功')
    loadHistory()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '推送失败')
  } finally {
    pushing.value = false
  }
}

// 预览报表
async function handlePreview() {
  if (manualPush.reportTypes.length === 0) {
    ElMessage.warning('请选择报表类型')
    return
  }

  showPreviewDialog.value = true
  loadingPreview.value = true
  try {
    previewData.value = await adminApi.previewReport({
      report_types: manualPush.reportTypes,
      days: manualPush.days
    })
  } catch (e) {
    ElMessage.error('加载预览失败')
  } finally {
    loadingPreview.value = false
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}
</script>

<style scoped>
.report-push {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

.setting-desc {
  margin-left: 12px;
  font-size: 13px;
  color: var(--text-muted, #94a3b8);
}

.form-tip {
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
  margin-top: 4px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 预览样式 */
.preview-section {
  margin-bottom: 24px;
}

.preview-section:last-child {
  margin-bottom: 0;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.overview-item {
  background: var(--bg-tertiary, #f1f5f9);
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.overview-item .label {
  display: block;
  font-size: 13px;
  color: var(--text-muted, #94a3b8);
  margin-bottom: 8px;
}

.overview-item .value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
}

/* 响应式 */
@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
