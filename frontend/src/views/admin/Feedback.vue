<template>
  <div class="feedback-page">
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总反馈数</div>
      </div>
      <div class="stat-card pending">
        <div class="stat-value">{{ stats.pending_count }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.by_type?.want || 0 }}</div>
        <div class="stat-label">想要工具</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.by_type?.suggestion || 0 }}</div>
        <div class="stat-label">建议改进</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="toolbar">
      <el-select
        v-model="filterStatus"
        placeholder="筛选状态"
        clearable
        style="width: 150px"
        @change="loadFeedback"
      >
        <el-option label="待处理" value="pending" />
        <el-option label="处理中" value="reviewing" />
        <el-option label="已完成" value="done" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      <el-select
        v-model="filterType"
        placeholder="筛选类型"
        clearable
        style="width: 150px; margin-left: 12px"
        @change="loadFeedback"
      >
        <el-option label="想要工具" value="want" />
        <el-option label="建议改进" value="suggestion" />
        <el-option label="问题反馈" value="issue" />
      </el-select>
    </div>

    <!-- 反馈列表 -->
    <el-table :data="feedbackList" v-loading="loading" stripe>
      <el-table-column type="index" label="#" width="60" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="getTypeTagType(row.feedback_type)" size="small">
            {{ getTypeName(row.feedback_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用户" width="120">
        <template #default="{ row }">
          {{ row.user_name || '匿名' }}
        </template>
      </el-table-column>
      <el-table-column label="内容" show-overflow-tooltip>
        <template #default="{ row }">
          <div v-if="row.feedback_type === 'want'" class="want-content">
            <strong>{{ row.tool_name }}</strong>
            <span v-if="row.tool_url" class="tool-url">{{ row.tool_url }}</span>
          </div>
          <div v-else>{{ row.content }}</div>
          <div v-if="row.feedback_type === 'want' && row.content" class="reason">
            理由: {{ row.content }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="关联工具" width="120">
        <template #default="{ row }">
          <span v-if="row.existing_tool_name">{{ row.existing_tool_name }}</span>
          <span v-else class="no-tool">-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)" size="small">
            {{ getStatusName(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="160">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text size="small" @click="handleProcess(row)">
            处理
          </el-button>
          <el-button
            v-if="row.admin_reply"
            type="info"
            text
            size="small"
            @click="handleViewReply(row)"
          >
            查看回复
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadFeedback"
      />
    </div>

    <!-- 处理弹窗 -->
    <el-dialog v-model="processDialogVisible" title="处理反馈" width="500px">
      <div class="feedback-detail" v-if="currentFeedback">
        <div class="detail-row">
          <span class="label">类型:</span>
          <el-tag :type="getTypeTagType(currentFeedback.feedback_type)" size="small">
            {{ getTypeName(currentFeedback.feedback_type) }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span class="label">用户:</span>
          <span>{{ currentFeedback.user_name || '匿名' }}</span>
        </div>
        <div class="detail-row" v-if="currentFeedback.feedback_type === 'want'">
          <span class="label">想要工具:</span>
          <span>{{ currentFeedback.tool_name }}</span>
        </div>
        <div class="detail-row" v-if="currentFeedback.tool_url">
          <span class="label">工具链接:</span>
          <a :href="currentFeedback.tool_url" target="_blank">{{ currentFeedback.tool_url }}</a>
        </div>
        <div class="detail-row" v-if="currentFeedback.content">
          <span class="label">内容:</span>
          <span>{{ currentFeedback.content }}</span>
        </div>
      </div>

      <el-divider />

      <el-form label-width="80px">
        <el-form-item label="状态">
          <el-select v-model="processForm.status" style="width: 100%">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="reviewing" />
            <el-option label="已完成" value="done" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="回复">
          <el-input
            v-model="processForm.admin_reply"
            type="textarea"
            :rows="3"
            placeholder="请输入回复内容（选填）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="processDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitProcess" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看回复弹窗 -->
    <el-dialog v-model="replyDialogVisible" title="管理员回复" width="400px">
      <p>{{ currentFeedback?.admin_reply }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { feedbackApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const feedbackList = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filterStatus = ref(null)
const filterType = ref(null)

const stats = ref({
  total: 0,
  pending_count: 0,
  by_status: {},
  by_type: {}
})

const processDialogVisible = ref(false)
const replyDialogVisible = ref(false)
const currentFeedback = ref(null)
const processForm = reactive({
  status: 'pending',
  admin_reply: ''
})

onMounted(async () => {
  await Promise.all([loadStats(), loadFeedback()])
})

async function loadStats() {
  try {
    stats.value = await feedbackApi.getStats()
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function loadFeedback() {
  try {
    loading.value = true
    const res = await feedbackApi.getList({
      page: page.value,
      size: size.value,
      status: filterStatus.value || undefined,
      feedback_type: filterType.value || undefined
    })
    feedbackList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('加载反馈列表失败:', error)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function getTypeName(type) {
  const map = {
    want: '想要工具',
    suggestion: '建议改进',
    issue: '问题反馈'
  }
  return map[type] || type
}

function getTypeTagType(type) {
  const map = {
    want: 'success',
    suggestion: 'primary',
    issue: 'warning'
  }
  return map[type] || 'info'
}

function getStatusName(status) {
  const map = {
    pending: '待处理',
    reviewing: '处理中',
    done: '已完成',
    rejected: '已拒绝'
  }
  return map[status] || status
}

function getStatusTagType(status) {
  const map = {
    pending: 'warning',
    reviewing: 'primary',
    done: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function handleProcess(row) {
  currentFeedback.value = row
  processForm.status = row.status
  processForm.admin_reply = row.admin_reply || ''
  processDialogVisible.value = true
}

function handleViewReply(row) {
  currentFeedback.value = row
  replyDialogVisible.value = true
}

async function handleSubmitProcess() {
  try {
    submitting.value = true
    await feedbackApi.update(currentFeedback.value.id, processForm)
    ElMessage.success('处理成功')
    processDialogVisible.value = false
    await Promise.all([loadStats(), loadFeedback()])
  } catch (error) {
    console.error('处理失败:', error)
    ElMessage.error('处理失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.feedback-page {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.stats-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-card.pending {
  background: #fef0f0;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-card.pending .stat-value {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.want-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-url {
  font-size: 12px;
  color: #909399;
}

.reason {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.no-tool {
  color: #c0c4cc;
}

.feedback-detail {
  padding: 0 20px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-row .label {
  width: 80px;
  flex-shrink: 0;
  color: #909399;
}

.detail-row a {
  color: #409eff;
  word-break: break-all;
}
</style>
