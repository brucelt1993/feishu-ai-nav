<template>
  <div class="stats-page">
    <!-- Tab容器：Tab和导出按钮在同一行 -->
    <div class="tab-container">
      <div class="tab-header">
        <el-tabs v-model="activeTab" class="stats-tabs" @tab-change="handleTabChange">
          <el-tab-pane label="工具点击" name="clicks" />
          <el-tab-pane label="工具互动" name="interactions" />
          <el-tab-pane label="提供者排行" name="providers" />
          <el-tab-pane label="用户分析" name="users" />
          <el-tab-pane label="用户想要" name="wants" />
        </el-tabs>

        <div class="header-actions">
          <!-- 时间筛选（仅工具点击和用户分析显示） -->
          <template v-if="activeTab === 'clicks' || activeTab === 'users'">
            <el-radio-group v-model="timeMode" size="small" @change="handleTimeModeChange">
              <el-radio-button value="today">今天</el-radio-button>
              <el-radio-button :value="7">7天</el-radio-button>
              <el-radio-button :value="14">14天</el-radio-button>
              <el-radio-button :value="30">30天</el-radio-button>
              <el-radio-button :value="90">90天</el-radio-button>
              <el-radio-button value="custom">自定义</el-radio-button>
            </el-radio-group>

            <!-- 自定义日期范围选择器 -->
            <el-date-picker
              v-if="timeMode === 'custom'"
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              :disabled-date="disabledDate"
              @change="handleDateRangeChange"
              style="width: 240px; margin-left: 8px;"
            />
          </template>

          <!-- 导出按钮 - 直接导出当前Tab -->
          <el-button type="primary" :loading="exporting" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </div>

      <!-- Tab内容区域 -->
      <div class="tab-content">
        <!-- 工具点击Tab -->
        <div v-show="activeTab === 'clicks'" class="tab-panel">
          <div class="panel-header">
            <h3 class="panel-title">工具点击排行 <span class="subtitle">Top 20</span></h3>
            <div class="sort-options">
              <span class="sort-label">排序：</span>
              <el-radio-group v-model="toolSortBy" size="small">
                <el-radio-button value="pv">PV</el-radio-button>
                <el-radio-button value="uv">UV</el-radio-button>
                <el-radio-button value="pv_trend">PV环比</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <el-table :data="sortedToolStats" stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="tool_name" label="工具名称" min-width="140" />
            <el-table-column prop="provider" label="提供者" width="100">
              <template #default="{ row }">
                <span class="provider-tag">{{ row.provider || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="click_count" label="PV" width="80" align="center" />
            <el-table-column prop="unique_users" label="UV" width="80" align="center" />
            <el-table-column label="PV环比" width="100" align="center">
              <template #default="{ row }">
                <TrendBadge :value="row.pv_trend" />
              </template>
            </el-table-column>
            <el-table-column label="UV环比" width="100" align="center">
              <template #default="{ row }">
                <TrendBadge :value="row.uv_trend" />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 工具互动Tab -->
        <div v-show="activeTab === 'interactions'" class="tab-panel">
          <div class="panel-header">
            <h3 class="panel-title">工具互动排行 <span class="subtitle">点赞 + 收藏</span></h3>
          </div>
          <el-table :data="interactionStats" stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="tool_name" label="工具名称" min-width="140" />
            <el-table-column prop="provider" label="提供者" width="100">
              <template #default="{ row }">
                <span class="provider-tag">{{ row.provider || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="favorite_count" label="收藏数" width="100" align="center">
              <template #default="{ row }">
                <span class="stat-cell favorite">
                  <el-icon><Star /></el-icon>
                  {{ row.favorite_count }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="like_count" label="点赞数" width="100" align="center">
              <template #default="{ row }">
                <span class="stat-cell like">
                  <el-icon><Pointer /></el-icon>
                  {{ row.like_count }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="total" label="总计" width="80" align="center">
              <template #default="{ row }">
                <span class="total-badge">{{ row.total }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 提供者排行Tab -->
        <div v-show="activeTab === 'providers'" class="tab-panel">
          <div class="panel-header">
            <h3 class="panel-title">提供者排行 <span class="subtitle">按贡献工具数</span></h3>
          </div>
          <el-table :data="providerStats" stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="provider" label="提供者" min-width="140">
              <template #default="{ row }">
                <span class="provider-name">{{ row.provider }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="tool_count" label="贡献工具数" width="120" align="center">
              <template #default="{ row }">
                <span class="count-badge tools">{{ row.tool_count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="click_count" label="总点击数" width="120" align="center">
              <template #default="{ row }">
                <span class="count-badge clicks">{{ row.click_count.toLocaleString() }}</span>
              </template>
            </el-table-column>
            <el-table-column label="平均点击" width="100" align="center">
              <template #default="{ row }">
                {{ row.tool_count > 0 ? Math.round(row.click_count / row.tool_count) : 0 }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 用户分析Tab -->
        <div v-show="activeTab === 'users'" class="tab-panel">
          <div class="panel-header">
            <h3 class="panel-title">用户活跃排行 <span class="subtitle">Top 20</span></h3>
            <div class="sort-options">
              <span class="sort-label">排序：</span>
              <el-radio-group v-model="userSortBy" size="small">
                <el-radio-button value="click_count">点击数</el-radio-button>
                <el-radio-button value="click_trend">环比</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <el-table :data="sortedUserStats" stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column label="用户" min-width="160">
              <template #default="{ row }">
                <div class="user-cell">
                  <el-avatar :src="row.avatar_url" :size="32">
                    {{ row.user_name?.charAt(0) }}
                  </el-avatar>
                  <span>{{ row.user_name || '未知用户' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="click_count" label="点击次数" width="100" align="center" />
            <el-table-column label="环比" width="100" align="center">
              <template #default="{ row }">
                <TrendBadge :value="row.click_trend" />
              </template>
            </el-table-column>
            <el-table-column prop="last_click" label="最后访问" width="160" />
          </el-table>
        </div>

        <!-- 用户想要Tab -->
        <div v-show="activeTab === 'wants'" class="tab-panel">
          <div class="panel-header">
            <h3 class="panel-title">用户想要 <span class="subtitle">按工具名称统计</span></h3>
          </div>
          <el-table :data="wantList" stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="tool_name" label="工具名称" min-width="200" />
            <el-table-column prop="want_count" label="想要次数" width="120" align="center">
              <template #default="{ row }">
                <span class="want-badge">{{ row.want_count }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Download, CaretTop, CaretBottom, Star, Pointer } from '@element-plus/icons-vue'

// 环比徽章组件
const TrendBadge = {
  props: { value: { type: Number, default: 0 } },
  setup(props) {
    const isUp = computed(() => props.value >= 0)
    const absValue = computed(() => Math.abs(props.value))
    return { isUp, absValue }
  },
  template: `
    <span class="trend-badge" :class="isUp ? 'up' : 'down'">
      <el-icon v-if="isUp"><CaretTop /></el-icon>
      <el-icon v-else><CaretBottom /></el-icon>
      {{ absValue }}%
    </span>
  `,
  components: { CaretTop, CaretBottom }
}

const activeTab = ref('clicks')
const timeMode = ref(7) // 'today' | 7 | 14 | 30 | 90 | 'custom'
const dateRange = ref(null)
const exporting = ref(false)
const toolSortBy = ref('pv')
const userSortBy = ref('click_count')

// 数据
const toolStats = ref([])
const userStats = ref([])
const interactionStats = ref([])
const providerStats = ref([])
const wantList = ref([])

// 计算实际天数
const effectiveDays = computed(() => {
  if (timeMode.value === 'today') return 1
  if (timeMode.value === 'custom' && dateRange.value) {
    const [start, end] = dateRange.value
    return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
  }
  return timeMode.value
})

// 排序后的数据
const sortedToolStats = computed(() => {
  const data = [...toolStats.value]
  switch (toolSortBy.value) {
    case 'pv': return data.sort((a, b) => b.click_count - a.click_count)
    case 'uv': return data.sort((a, b) => b.unique_users - a.unique_users)
    case 'pv_trend': return data.sort((a, b) => b.pv_trend - a.pv_trend)
    default: return data
  }
})

const sortedUserStats = computed(() => {
  const data = [...userStats.value]
  switch (userSortBy.value) {
    case 'click_count': return data.sort((a, b) => b.click_count - a.click_count)
    case 'click_trend': return data.sort((a, b) => b.click_trend - a.click_trend)
    default: return data
  }
})

// 禁用超过3个月的日期
function disabledDate(date) {
  const now = new Date()
  const threeMonthsAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
  return date > now || date < threeMonthsAgo
}

onMounted(() => {
  loadAllData()
})

async function loadAllData() {
  await Promise.all([
    loadToolStats(),
    loadUserStats(),
    loadInteractionStats(),
    loadProviderStats(),
    loadWantList()
  ])
}

function handleTabChange(tab) {
  // Tab切换时可以按需加载数据
}

function handleTimeModeChange() {
  if (timeMode.value !== 'custom') {
    dateRange.value = null
    loadCurrentTabData()
  }
}

function handleDateRangeChange() {
  if (dateRange.value && dateRange.value.length === 2) {
    loadCurrentTabData()
  }
}

function loadCurrentTabData() {
  if (activeTab.value === 'clicks') {
    loadToolStats()
  } else if (activeTab.value === 'users') {
    loadUserStats()
  }
}

async function loadToolStats() {
  try {
    toolStats.value = await adminApi.getToolStats(effectiveDays.value, 20)
  } catch (error) {
    console.error('加载工具统计失败:', error)
  }
}

async function loadUserStats() {
  try {
    userStats.value = await adminApi.getUserStats(effectiveDays.value, 20)
  } catch (error) {
    console.error('加载用户统计失败:', error)
  }
}

async function loadInteractionStats() {
  try {
    interactionStats.value = await adminApi.getToolInteractions(20)
  } catch (error) {
    console.error('加载互动统计失败:', error)
  }
}

async function loadProviderStats() {
  try {
    providerStats.value = await adminApi.getProviderStats(20)
  } catch (error) {
    console.error('加载提供者统计失败:', error)
  }
}

async function loadWantList() {
  try {
    wantList.value = await adminApi.getWantList(50)
  } catch (error) {
    console.error('加载想要列表失败:', error)
  }
}

async function handleExport() {
  exporting.value = true
  try {
    let blob, filename
    const today = new Date().toISOString().split('T')[0]

    switch (activeTab.value) {
      case 'clicks':
        blob = await adminApi.exportToolsStats(effectiveDays.value)
        filename = `tools_clicks_${today}.xlsx`
        break
      case 'interactions':
        blob = await adminApi.exportInteractionsStats()
        filename = `tools_interactions_${today}.xlsx`
        break
      case 'providers':
        blob = await adminApi.exportProvidersStats()
        filename = `providers_stats_${today}.xlsx`
        break
      case 'users':
        blob = await adminApi.exportUsersStats(effectiveDays.value)
        filename = `users_stats_${today}.xlsx`
        break
      case 'wants':
        blob = await adminApi.exportWantsStats()
        filename = `wants_stats_${today}.xlsx`
        break
    }

    downloadBlob(blob, filename)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(new Blob([blob]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
</script>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tab-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.tab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #f0f0f0;
}

.stats-tabs {
  flex: 1;
}

.stats-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.stats-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.stats-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  height: 56px;
  line-height: 56px;
}

.stats-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
}

.stats-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.tab-content {
  padding: 20px;
}

.tab-panel {
  min-height: 400px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.panel-title .subtitle {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 400;
  margin-left: 8px;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-label {
  font-size: 13px;
  color: #64748b;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.provider-tag {
  color: #64748b;
  font-size: 13px;
}

.provider-name {
  font-weight: 500;
  color: #1e293b;
}

.stat-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.stat-cell.favorite {
  color: #f59e0b;
}

.stat-cell.like {
  color: #667eea;
}

.total-badge {
  display: inline-block;
  padding: 2px 10px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.want-badge {
  display: inline-block;
  padding: 4px 14px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.count-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
}

.count-badge.tools {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.count-badge.clicks {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

/* 环比徽章 */
:deep(.trend-badge) {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 12px;
}

:deep(.trend-badge.up) {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

:deep(.trend-badge.down) {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

:deep(.trend-badge .el-icon) {
  font-size: 12px;
}

@media (max-width: 1200px) {
  .tab-header {
    flex-direction: column;
    align-items: stretch;
    padding: 0;
  }

  .stats-tabs {
    border-bottom: 1px solid #f0f0f0;
  }

  .header-actions {
    padding: 12px 20px;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
