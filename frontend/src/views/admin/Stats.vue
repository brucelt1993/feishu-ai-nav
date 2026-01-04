<template>
  <div class="stats-page">
    <!-- 筛选条件 + 导出按钮 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-radio-group v-model="days" @change="loadData">
          <el-radio-button :value="7">近7天</el-radio-button>
          <el-radio-button :value="14">近14天</el-radio-button>
          <el-radio-button :value="30">近30天</el-radio-button>
          <el-radio-button :value="90">近90天</el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-right">
        <el-dropdown @command="handleExport" :disabled="exporting">
          <el-button type="primary" :loading="exporting">
            <el-icon><Download /></el-icon>
            导出报表
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="tools">
                <el-icon><Tools /></el-icon>
                工具统计报表
              </el-dropdown-item>
              <el-dropdown-item command="users">
                <el-icon><User /></el-icon>
                用户统计报表
              </el-dropdown-item>
              <el-dropdown-item command="trend">
                <el-icon><TrendCharts /></el-icon>
                趋势统计报表
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 趋势图 -->
    <div class="chart-card">
      <h3 class="card-title">使用趋势</h3>
      <div ref="trendChart" class="chart-container"></div>
    </div>

    <!-- 图表行：分类分布 + 工具排行 -->
    <div class="chart-row">
      <div class="chart-card half">
        <h3 class="card-title">分类使用分布</h3>
        <div ref="categoryChart" class="chart-container-small"></div>
      </div>

      <div class="rank-card half">
        <h3 class="card-title">
          工具使用排行
          <span class="card-subtitle">Top 20</span>
        </h3>
        <el-table :data="toolStats" stripe size="small" max-height="320">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="tool_name" label="工具名称" min-width="120" />
          <el-table-column prop="click_count" label="PV" width="80" align="center" />
          <el-table-column prop="unique_users" label="UV" width="80" align="center" />
          <el-table-column label="占比" width="100">
            <template #default="{ row }">
              <el-progress
                :percentage="getPercentage(row.click_count, toolTotal)"
                :stroke-width="8"
                :show-text="false"
                color="#667eea"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 用户排行 -->
    <div class="rank-card">
      <h3 class="card-title">
        用户活跃排行
        <span class="card-subtitle">Top 20</span>
      </h3>
      <el-table :data="userStats" stripe size="small">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column label="用户" min-width="160">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :src="row.avatar_url" :size="28">
                {{ row.user_name?.charAt(0) }}
              </el-avatar>
              <span>{{ row.user_name || '未知用户' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="click_count" label="点击次数" width="100" align="center" />
        <el-table-column prop="last_click" label="最后访问" width="160" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'
import { adminApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Download, ArrowDown, Tools, User, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const days = ref(7)
const trendChart = ref(null)
const categoryChart = ref(null)
const toolStats = ref([])
const userStats = ref([])
const categoryData = ref([])
const exporting = ref(false)

let trendChartInstance = null
let categoryChartInstance = null
let resizeHandler = null

const toolTotal = computed(() => {
  return toolStats.value.reduce((sum, t) => sum + t.click_count, 0)
})

onMounted(() => {
  loadData()
  // 监听窗口resize
  resizeHandler = () => {
    trendChartInstance?.resize()
    categoryChartInstance?.resize()
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  cleanupCharts()
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})

// keep-alive 支持
onActivated(() => {
  trendChartInstance?.resize()
  categoryChartInstance?.resize()
})

onDeactivated(() => {
  // 暂停时不需要特殊处理
})

function cleanupCharts() {
  trendChartInstance?.dispose()
  categoryChartInstance?.dispose()
  trendChartInstance = null
  categoryChartInstance = null
}

async function loadData() {
  await Promise.all([
    loadTrend(),
    loadToolStats(),
    loadUserStats(),
    loadCategoryDistribution()
  ])
}

async function loadTrend() {
  try {
    const data = await adminApi.getTrend(days.value)
    renderTrendChart(data)
  } catch (error) {
    console.error('加载趋势失败:', error)
  }
}

async function loadToolStats() {
  try {
    toolStats.value = await adminApi.getToolStats(days.value, 20)
  } catch (error) {
    console.error('加载工具统计失败:', error)
  }
}

async function loadUserStats() {
  try {
    userStats.value = await adminApi.getUserStats(days.value, 20)
  } catch (error) {
    console.error('加载用户统计失败:', error)
  }
}

async function loadCategoryDistribution() {
  try {
    categoryData.value = await adminApi.getCategoryDistribution()
    renderCategoryChart(categoryData.value)
  } catch (error) {
    console.error('加载分类分布失败:', error)
  }
}

function renderTrendChart(data) {
  if (!trendChart.value) return

  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: { data: ['PV', 'UV'] },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(d => d.date)
    },
    yAxis: [
      { type: 'value', name: 'PV' },
      { type: 'value', name: 'UV' }
    ],
    series: [
      {
        name: 'PV',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: data.map(d => d.pv),
        itemStyle: { color: '#667eea' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
            { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
          ])
        }
      },
      {
        name: 'UV',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map(d => d.uv),
        itemStyle: { color: '#67c23a' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
          ])
        }
      }
    ]
  })
}

function renderCategoryChart(data) {
  if (!categoryChart.value) return

  if (!categoryChartInstance) {
    categoryChartInstance = echarts.init(categoryChart.value)
  }

  const chartData = data.map(item => ({
    name: item.category_name,
    value: item.click_count,
    itemStyle: { color: item.color || '#667eea' }
  }))

  categoryChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      type: 'scroll'
    },
    series: [
      {
        name: '分类使用',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: chartData
      }
    ]
  })
}

async function handleExport(command) {
  exporting.value = true
  try {
    let blob, filename
    const today = new Date().toISOString().split('T')[0]

    switch (command) {
      case 'tools':
        blob = await adminApi.exportToolsStats(days.value)
        filename = `tools_stats_${today}.xlsx`
        break
      case 'users':
        blob = await adminApi.exportUsersStats(days.value)
        filename = `users_stats_${today}.xlsx`
        break
      case 'trend':
        blob = await adminApi.exportTrendStats(days.value)
        filename = `trend_stats_${today}.xlsx`
        break
    }

    // 下载文件
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

function getPercentage(value, total) {
  if (!total) return 0
  return Math.round((value / total) * 100)
}
</script>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-card,
.rank-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.card-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-subtitle {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}

.chart-container {
  height: 350px;
}

.chart-container-small {
  height: 320px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-row .half {
  min-width: 0;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-cell .el-avatar {
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .filter-left,
  .filter-right {
    justify-content: center;
  }
}
</style>
