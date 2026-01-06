<template>
  <div class="dashboard">
    <!-- 统计卡片区域 - 8卡片 2行4列 -->
    <div class="stat-cards-grid">
      <StatCard
        v-for="(card, index) in statCards"
        :key="card.key"
        :value="card.value"
        :label="card.label"
        :icon="card.icon"
        :color-class="card.colorClass"
        :trend="card.trend"
        :style="{ animationDelay: `${index * 0.1}s` }"
        class="stat-card-animate"
      />
    </div>

    <!-- 使用趋势图 -->
    <div class="chart-section">
      <div class="section-header">
        <h3 class="section-title">使用趋势</h3>
        <div class="section-actions">
          <el-radio-group v-model="trendDays" size="small" @change="loadTrend">
            <el-radio-button :value="7">7天</el-radio-button>
            <el-radio-button :value="14">14天</el-radio-button>
            <el-radio-button :value="30">30天</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div ref="trendChart" class="chart-container"></div>
    </div>

    <!-- 图表行 -->
    <div class="chart-row">
      <!-- 分类分布 -->
      <div class="chart-section half">
        <div class="section-header">
          <h3 class="section-title">分类分布</h3>
        </div>
        <div ref="categoryChart" class="chart-container-half"></div>
      </div>

      <!-- 工具排行 -->
      <div class="chart-section half">
        <div class="section-header">
          <h3 class="section-title">工具排行 TOP10</h3>
          <el-radio-group v-model="toolDays" size="small" @change="loadToolStats">
            <el-radio-button :value="7">7天</el-radio-button>
            <el-radio-button :value="30">30天</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="toolChart" class="chart-container-half"></div>
      </div>
    </div>

    <!-- 活跃用户 -->
    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">活跃用户 TOP20</h3>
        <el-radio-group v-model="userDays" size="small" @change="loadUserStats">
          <el-radio-button :value="7">7天</el-radio-button>
          <el-radio-button :value="30">30天</el-radio-button>
        </el-radio-group>
      </div>
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
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'
import { adminApi } from '@/api'
import * as echarts from 'echarts'
import StatCard from '@/components/admin/StatCard.vue'
import { View, User, Histogram, UserFilled, Plus, Timer, Star, Pointer } from '@element-plus/icons-vue'

// 统计数据
const stats = ref({})
const userStats = ref([])
const categoryData = ref([])

// 时间筛选
const trendDays = ref(30)
const toolDays = ref(7)
const userDays = ref(7)

// 图表引用
const trendChart = ref(null)
const toolChart = ref(null)
const categoryChart = ref(null)

let trendChartInstance = null
let toolChartInstance = null
let categoryChartInstance = null
let resizeHandler = null

// 统计卡片配置
const statCards = computed(() => [
  {
    key: 'today_pv',
    label: '今日PV',
    value: stats.value.today_pv || 0,
    trend: stats.value.today_pv_trend,
    icon: View,
    colorClass: 'purple'
  },
  {
    key: 'today_uv',
    label: '今日UV',
    value: stats.value.today_uv || 0,
    trend: stats.value.today_uv_trend,
    icon: User,
    colorClass: 'green'
  },
  {
    key: 'total_pv',
    label: '总PV',
    value: stats.value.total_pv || 0,
    icon: Histogram,
    colorClass: 'orange'
  },
  {
    key: 'total_uv',
    label: '总UV',
    value: stats.value.total_uv || 0,
    icon: UserFilled,
    colorClass: 'red'
  },
  {
    key: 'new_users',
    label: '今日新增',
    value: stats.value.new_users_today || 0,
    trend: stats.value.new_users_trend,
    icon: Plus,
    colorClass: 'cyan'
  },
  {
    key: 'active_users',
    label: '7日活跃',
    value: stats.value.active_users_7d || 0,
    icon: Timer,
    colorClass: 'violet'
  },
  {
    key: 'favorites',
    label: '总收藏',
    value: stats.value.total_favorites || 0,
    icon: Star,
    colorClass: 'pink'
  },
  {
    key: 'likes',
    label: '总点赞',
    value: stats.value.total_likes || 0,
    icon: Pointer,
    colorClass: 'rose'
  }
])

// 图表配色
const CHART_COLORS = {
  primary: '#667eea',
  secondary: '#764ba2',
  success: '#10b981',
  pieColors: [
    '#667eea', '#10b981', '#f59e0b', '#ef4444',
    '#06b6d4', '#8b5cf6', '#ec4899', '#84cc16'
  ]
}

onMounted(async () => {
  await Promise.all([
    loadOverview(),
    loadTrend(),
    loadToolStats(),
    loadUserStats(),
    loadCategoryDistribution()
  ])

  resizeHandler = () => {
    trendChartInstance?.resize()
    toolChartInstance?.resize()
    categoryChartInstance?.resize()
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
  trendChartInstance?.dispose()
  toolChartInstance?.dispose()
  categoryChartInstance?.dispose()
  trendChartInstance = null
  toolChartInstance = null
  categoryChartInstance = null
})

onActivated(() => {
  trendChartInstance?.resize()
  toolChartInstance?.resize()
  categoryChartInstance?.resize()
})

onDeactivated(() => {})

async function loadOverview() {
  try {
    stats.value = await adminApi.getExtendedOverview()
  } catch (error) {
    console.error('加载概览失败:', error)
    // 降级使用旧接口
    try {
      stats.value = await adminApi.getOverview()
    } catch (e) {
      console.error('降级加载也失败:', e)
    }
  }
}

async function loadTrend() {
  try {
    const data = await adminApi.getTrend(trendDays.value)
    renderTrendChart(data)
  } catch (error) {
    console.error('加载趋势失败:', error)
  }
}

async function loadToolStats() {
  try {
    const data = await adminApi.getToolStats(toolDays.value, 10)
    renderToolChart(data)
  } catch (error) {
    console.error('加载工具统计失败:', error)
  }
}

async function loadUserStats() {
  try {
    userStats.value = await adminApi.getUserStats(userDays.value, 20)
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
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b' }
    },
    legend: {
      data: ['PV', 'UV'],
      right: 20,
      top: 0
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 40, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(d => d.date),
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b' }
    },
    series: [
      {
        name: 'PV',
        type: 'line',
        smooth: true,
        data: data.map(d => d.pv),
        lineStyle: { color: CHART_COLORS.primary, width: 3 },
        itemStyle: { color: CHART_COLORS.primary },
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
        data: data.map(d => d.uv),
        lineStyle: { color: CHART_COLORS.success, width: 3 },
        itemStyle: { color: CHART_COLORS.success },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
          ])
        }
      }
    ]
  })
}

function renderToolChart(data) {
  if (!toolChart.value) return

  if (!toolChartInstance) {
    toolChartInstance = echarts.init(toolChart.value)
  }

  toolChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b' }
    },
    grid: { left: '3%', right: '8%', bottom: '3%', top: 10, containLabel: true },
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.tool_name).reverse(),
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' }
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.click_count).reverse(),
      barWidth: 16,
      itemStyle: {
        borderRadius: [0, 8, 8, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: CHART_COLORS.primary },
          { offset: 1, color: CHART_COLORS.secondary }
        ])
      }
    }]
  })
}

function renderCategoryChart(data) {
  if (!categoryChart.value || !data.length) return

  if (!categoryChartInstance) {
    categoryChartInstance = echarts.init(categoryChart.value)
  }

  const total = data.reduce((sum, d) => sum + d.click_count, 0)

  categoryChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b' },
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 20,
      top: 'center',
      textStyle: { color: '#64748b' }
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 18,
          fontWeight: 'bold',
          formatter: '{b}\n{d}%'
        }
      },
      labelLine: { show: false },
      data: data.map((d, i) => ({
        value: d.click_count,
        name: d.category_name,
        itemStyle: { color: d.color || CHART_COLORS.pieColors[i % CHART_COLORS.pieColors.length] }
      }))
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

/* 8卡片网格布局 */
.stat-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

/* 卡片入场动画 */
.stat-card-animate {
  opacity: 0;
  animation: fadeInUp 0.5s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 图表区块 */
.chart-section,
.table-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.chart-container {
  height: 320px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-section.half {
  min-width: 0;
}

.chart-container-half {
  height: 280px;
}

/* 响应式布局 */
@media (max-width: 1400px) {
  .stat-cards-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1200px) {
  .stat-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stat-cards-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
