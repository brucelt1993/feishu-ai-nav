<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: #409eff;">
          <el-icon><View /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today_pv || 0 }}</div>
          <div class="stat-label">今日PV</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: #67c23a;">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today_uv || 0 }}</div>
          <div class="stat-label">今日UV</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: #e6a23c;">
          <el-icon><Histogram /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_clicks || 0 }}</div>
          <div class="stat-label">总点击</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: #f56c6c;">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_users || 0 }}</div>
          <div class="stat-label">总用户</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">使用趋势</h3>
        <div ref="trendChart" class="chart-container"></div>
      </div>

      <div class="chart-card">
        <h3 class="chart-title">工具排行 TOP10</h3>
        <div ref="toolChart" class="chart-container"></div>
      </div>
    </div>

    <!-- 活跃用户 -->
    <div class="table-card">
      <h3 class="chart-title">活跃用户 TOP20</h3>
      <el-table :data="userStats" stripe>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="user_name" label="用户" />
        <el-table-column prop="click_count" label="点击次数" width="120" />
        <el-table-column prop="last_click" label="最后访问" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'
import { ElMessage } from 'element-plus'
import { View, User, Histogram, UserFilled } from '@element-plus/icons-vue'
import { adminApi } from '@/api'
import * as echarts from 'echarts'

const stats = ref({})
const userStats = ref([])
const trendChart = ref(null)
const toolChart = ref(null)

let trendChartInstance = null
let toolChartInstance = null
let resizeHandler = null

onMounted(async () => {
  await Promise.all([
    loadOverview(),
    loadTrend(),
    loadToolStats(),
    loadUserStats()
  ])

  // 监听窗口resize，响应式调整图表
  resizeHandler = () => {
    trendChartInstance?.resize()
    toolChartInstance?.resize()
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  // 清理resize事件监听
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
  // 销毁图表实例
  if (trendChartInstance) {
    trendChartInstance.dispose()
    trendChartInstance = null
  }
  if (toolChartInstance) {
    toolChartInstance.dispose()
    toolChartInstance = null
  }
})

// keep-alive 支持
onActivated(() => {
  trendChartInstance?.resize()
  toolChartInstance?.resize()
})

onDeactivated(() => {
  // 组件被缓存时暂停可能的动画
})

async function loadOverview() {
  try {
    stats.value = await adminApi.getOverview()
  } catch (error) {
    console.error('加载概览失败:', error)
  }
}

async function loadTrend() {
  try {
    const data = await adminApi.getTrend(30)
    renderTrendChart(data)
  } catch (error) {
    console.error('加载趋势失败:', error)
  }
}

async function loadToolStats() {
  try {
    const data = await adminApi.getToolStats(7, 10)
    renderToolChart(data)
  } catch (error) {
    console.error('加载工具统计失败:', error)
  }
}

async function loadUserStats() {
  try {
    userStats.value = await adminApi.getUserStats(7, 20)
  } catch (error) {
    console.error('加载用户统计失败:', error)
  }
}

function renderTrendChart(data) {
  if (!trendChart.value) return

  trendChartInstance = echarts.init(trendChart.value)
  trendChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PV', 'UV'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(d => d.date)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'PV',
        type: 'line',
        smooth: true,
        data: data.map(d => d.pv),
        areaStyle: { opacity: 0.3 }
      },
      {
        name: 'UV',
        type: 'line',
        smooth: true,
        data: data.map(d => d.uv),
        areaStyle: { opacity: 0.3 }
      }
    ]
  })
}

function renderToolChart(data) {
  if (!toolChart.value) return

  toolChartInstance = echarts.init(toolChart.value)
  toolChartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: data.map(d => d.tool_name).reverse()
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.click_count).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' }
        ])
      }
    }]
  })
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-card,
.table-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.chart-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.chart-container {
  height: 300px;
}

@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-row {
    grid-template-columns: 1fr;
  }
}
</style>
