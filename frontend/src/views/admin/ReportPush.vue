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

        <template v-if="pushSettings.enabled">
          <el-form-item label="推送时间">
            <el-time-picker
              v-model="pushSettings.pushTime"
              format="HH:mm"
              placeholder="选择推送时间"
            />
          </el-form-item>

          <el-form-item label="报表类型">
            <el-checkbox-group v-model="pushSettings.reportTypes">
              <el-checkbox label="clicks">工具点击</el-checkbox>
              <el-checkbox label="interactions">工具互动</el-checkbox>
              <el-checkbox label="providers">提供者排行</el-checkbox>
              <el-checkbox label="users">用户分析</el-checkbox>
              <el-checkbox label="wants">用户想要</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="统计周期">
            <el-radio-group v-model="pushSettings.days">
              <el-radio :label="1">今天</el-radio>
              <el-radio :label="7">近7天</el-radio>
              <el-radio :label="30">近30天</el-radio>
            </el-radio-group>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 推送人员和群聊管理 -->
    <el-card class="recipients-card">
      <template #header>
        <div class="card-header">
          <span>推送目标</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加人员
          </el-button>
        </div>
      </template>

      <!-- 群聊选择 -->
      <div class="section-title">
        <el-icon><ChatDotRound /></el-icon>
        群聊
        <el-button text size="small" @click="loadChats" :loading="loadingChats">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      <div class="chat-list" v-loading="loadingChats">
        <el-checkbox-group v-model="selectedChatIds" v-if="chatList.length">
          <el-checkbox
            v-for="chat in chatList"
            :key="chat.chat_id"
            :label="chat.chat_id"
            class="chat-item"
          >
            <div class="chat-info">
              <el-avatar :size="24" :src="chat.avatar">
                <el-icon><ChatDotSquare /></el-icon>
              </el-avatar>
              <span class="chat-name">{{ chat.name }}</span>
            </div>
          </el-checkbox>
        </el-checkbox-group>
        <el-empty v-else description="暂无已加入的群聊" :image-size="60" />
      </div>

      <!-- 人员列表 -->
      <div class="section-title" style="margin-top: 24px;">
        <el-icon><User /></el-icon>
        人员
      </div>
      <el-table :data="recipients" v-loading="loadingRecipients" empty-text="暂无推送人员" size="small">
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="toggleStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">
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
            <el-checkbox label="clicks">工具点击</el-checkbox>
            <el-checkbox label="interactions">工具互动</el-checkbox>
            <el-checkbox label="providers">提供者排行</el-checkbox>
            <el-checkbox label="users">用户分析</el-checkbox>
            <el-checkbox label="wants">用户想要</el-checkbox>
            <el-checkbox label="custom">自定义通知</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 自定义内容输入框 -->
        <el-form-item label="自定义内容" v-if="manualPush.reportTypes.includes('custom')">
          <el-input
            v-model="manualPush.customContent"
            type="textarea"
            :rows="3"
            placeholder="请输入自定义通知内容，如：最新上新了几款AI工具，通知到各位"
          />
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
          <div class="form-tip" v-if="manualPush.method === 'email'">
            邮件仅发送给人员，不支持群聊
          </div>
        </el-form-item>

        <el-form-item label="推送目标">
          <div class="push-target-summary">
            <el-tag v-if="selectedChatIds.length" type="primary" size="small">
              {{ selectedChatIds.length }} 个群聊
            </el-tag>
            <el-tag v-if="activeRecipientCount" type="success" size="small">
              {{ activeRecipientCount }} 位人员
            </el-tag>
            <span v-if="!selectedChatIds.length && !activeRecipientCount" class="no-target">
              未选择推送目标
            </span>
          </div>
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
        <el-table-column prop="report_type" label="报表类型" min-width="150">
          <template #default="{ row }">
            {{ formatReportTypes(row.report_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="push_method" label="推送方式" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.push_method === 'feishu' ? 'primary' : 'success'">
              {{ row.push_method === 'feishu' ? '飞书' : '邮件' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="recipient_count" label="接收数" width="80" />
        <el-table-column label="状态" width="80">
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
    <el-dialog v-model="showPreviewDialog" title="报表预览" width="900px">
      <div class="preview-content" v-loading="loadingPreview">
        <div v-if="previewData">
          <!-- 自定义通知 -->
          <div class="preview-section" v-if="previewData.custom">
            <h4><el-icon><Bell /></el-icon> 自定义通知</h4>
            <div class="custom-content">
              {{ previewData.custom.content }}
            </div>
          </div>

          <!-- 工具点击 -->
          <div class="preview-section" v-if="previewData.clicks?.length">
            <h4><el-icon><DataLine /></el-icon> 工具点击 TOP10</h4>
            <el-table :data="previewData.clicks" size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="tool_name" label="工具名称" />
              <el-table-column prop="provider" label="提供者" width="100" />
              <el-table-column prop="click_count" label="PV" width="80" />
              <el-table-column prop="unique_users" label="UV" width="80" />
              <el-table-column label="PV环比" width="100">
                <template #default="{ row }">
                  <span :class="row.pv_trend >= 0 ? 'trend-up' : 'trend-down'">
                    {{ row.pv_trend >= 0 ? '+' : '' }}{{ row.pv_trend }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 工具互动 -->
          <div class="preview-section" v-if="previewData.interactions?.length">
            <h4><el-icon><Star /></el-icon> 工具互动 TOP10</h4>
            <el-table :data="previewData.interactions" size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="tool_name" label="工具名称" />
              <el-table-column prop="provider" label="提供者" width="100" />
              <el-table-column prop="favorite_count" label="收藏" width="80" />
              <el-table-column prop="like_count" label="点赞" width="80" />
              <el-table-column prop="total" label="总计" width="80" />
            </el-table>
          </div>

          <!-- 提供者排行 -->
          <div class="preview-section" v-if="previewData.providers?.length">
            <h4><el-icon><Trophy /></el-icon> 提供者排行 TOP10</h4>
            <el-table :data="previewData.providers" size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="provider" label="提供者" />
              <el-table-column prop="tool_count" label="工具数" width="100" />
              <el-table-column prop="click_count" label="点击数" width="100" />
            </el-table>
          </div>

          <!-- 用户分析 -->
          <div class="preview-section" v-if="previewData.users?.length">
            <h4><el-icon><User /></el-icon> 活跃用户 TOP10</h4>
            <el-table :data="previewData.users" size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="user_name" label="用户名" />
              <el-table-column prop="click_count" label="点击次数" width="100" />
              <el-table-column label="环比" width="100">
                <template #default="{ row }">
                  <span :class="row.click_trend >= 0 ? 'trend-up' : 'trend-down'">
                    {{ row.click_trend >= 0 ? '+' : '' }}{{ row.click_trend }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="last_click" label="最后访问" width="150" />
            </el-table>
          </div>

          <!-- 用户想要 -->
          <div class="preview-section" v-if="previewData.wants?.length">
            <h4><el-icon><Pointer /></el-icon> 用户想要 TOP10</h4>
            <el-table :data="previewData.wants" size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="tool_name" label="工具名称" />
              <el-table-column prop="want_count" label="想要次数" width="100" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Promotion, View, Refresh, User,
  ChatDotRound, ChatDotSquare, Bell, DataLine,
  Star, Trophy, Pointer
} from '@element-plus/icons-vue'
import { adminApi } from '@/api'

// 报表类型映射
const REPORT_TYPE_NAMES = {
  clicks: '工具点击',
  interactions: '工具互动',
  providers: '提供者排行',
  users: '用户分析',
  wants: '用户想要',
  custom: '自定义通知',
  // 兼容旧数据
  overview: '数据概览',
  tools: '工具排行',
  trend: '使用趋势'
}

// 推送设置
const pushSettings = reactive({
  enabled: false,
  pushTime: null,
  reportTypes: ['clicks', 'users'],
  days: 7
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

// 群聊
const chatList = ref([])
const loadingChats = ref(false)
const selectedChatIds = ref([])

// 活跃人员数量
const activeRecipientCount = computed(() => {
  return recipients.value.filter(r => r.is_active).length
})

// 手动推送
const manualPush = reactive({
  reportTypes: ['clicks', 'users'],
  days: 7,
  method: 'feishu',
  customContent: ''
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
  loadChats()
  loadHistory()
})

// 加载群聊列表
async function loadChats() {
  loadingChats.value = true
  try {
    chatList.value = await adminApi.getBotChats()
  } catch (e) {
    console.error('加载群聊列表失败:', e)
  } finally {
    loadingChats.value = false
  }
}

// 加载设置
async function loadSettings() {
  try {
    const data = await adminApi.getReportPushSettings()
    pushSettings.enabled = data.enabled
    // 将旧类型映射到新类型
    const oldToNew = { overview: 'clicks', tools: 'clicks', trend: 'users' }
    const types = (data.report_types || ['clicks', 'users']).map(t => oldToNew[t] || t)
    pushSettings.reportTypes = [...new Set(types)]
    pushSettings.days = data.days || 7
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
      push_time: pushTime,
      report_types: pushSettings.reportTypes,
      days: pushSettings.days
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

  if (manualPush.reportTypes.includes('custom') && !manualPush.customContent.trim()) {
    ElMessage.warning('请输入自定义通知内容')
    return
  }

  if (selectedChatIds.value.length === 0 && activeRecipientCount.value === 0) {
    ElMessage.warning('请选择推送目标（群聊或人员）')
    return
  }

  pushing.value = true
  try {
    await adminApi.pushReport({
      report_types: manualPush.reportTypes,
      days: manualPush.days,
      method: manualPush.method,
      chat_ids: selectedChatIds.value,
      custom_content: manualPush.reportTypes.includes('custom') ? manualPush.customContent : null
    })
    ElMessage.success('推送任务已提交')
    // 后台任务需要时间执行，延迟刷新历史
    setTimeout(() => {
      loadHistory()
    }, 3000)
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
      days: manualPush.days,
      custom_content: manualPush.reportTypes.includes('custom') ? manualPush.customContent : null
    })
  } catch (e) {
    ElMessage.error('加载预览失败')
  } finally {
    loadingPreview.value = false
  }
}

// 格式化报表类型
function formatReportTypes(types) {
  if (!types) return ''
  return types.split(',').map(t => REPORT_TYPE_NAMES[t] || t).join('、')
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

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin-bottom: 12px;
}

.section-title .el-icon {
  color: #667eea;
}

.chat-list {
  background: var(--bg-tertiary, #f8fafc);
  border-radius: 12px;
  padding: 16px;
  min-height: 80px;
}

.chat-list .el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.chat-item {
  margin-right: 0 !important;
}

.chat-item :deep(.el-checkbox__label) {
  padding-left: 8px;
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-name {
  font-size: 13px;
}

.push-target-summary {
  display: flex;
  align-items: center;
  gap: 8px;
}

.no-target {
  font-size: 13px;
  color: var(--text-muted, #94a3b8);
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-section h4 .el-icon {
  color: #667eea;
}

.custom-content {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  padding: 16px;
  border-radius: 12px;
  font-size: 14px;
  color: var(--text-primary, #1e293b);
  line-height: 1.6;
  border-left: 4px solid #667eea;
}

.trend-up {
  color: #10b981;
  font-weight: 500;
}

.trend-down {
  color: #ef4444;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-list .el-checkbox-group {
    flex-direction: column;
  }
}
</style>
