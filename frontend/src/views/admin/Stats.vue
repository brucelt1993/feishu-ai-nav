<template>
  <div class="stats-page">
    <!-- 筛选条件 -->
    <div class="filter-bar">
      <el-radio-group v-model="days" @change="loadData">
        <el-radio-button :value="7">近7天</el-radio-button>
        <el-radio-button :value="14">近14天</el-radio-button>
        <el-radio-button :value="30">近30天</el-radio-button>
        <el-radio-button :value="90">近90天</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 趋势图 -->
    <div class="chart-card">
      <h3 class="card-title">使用趋势</h3>
      <div ref="trendChart" class="chart-container"></div>
    </div>

    <!-- 排行榜 -->
    <div class="rank-row">
      <div class="rank-card">
        <h3 class="card-title">工具使用排行</h3>
        <el-table :data="toolStats" stripe size="small">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="name" label="工具名称" />
          <el-table-column prop="click_count" label="点击次数" width="100" />
          <el-table-column label="占比" width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="getPercentage(row.click_count, toolTotal)"
                :stroke-width="10"
                :show-text="false"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="rank-card">
        <h3 class="card-title">用户活跃排行</h3>
        <el-table :data="userStats" stripe size="small">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="name" label="用户" />
          <el-table-column prop="click_count" label="点击次数" width="100" />
          <el-table-column prop="last_click" label="最后访问" width="160" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { adminApi } from '@/api'
import * as echarts from 'echarts'

const days = ref(7)
const trendChart = ref(null)
const toolStats = ref([])
const userStats = ref([])

let chartInstance = null

const toolTotal = computed(() => {
  return toolStats.value.reduce((sum, t) => sum + t.click_count, 0)
})

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  chartInstance?.dispose()
})

async function loadData() {
  await Promise.all([
    loadTrend(),
    loadToolStats(),
    loadUserStats()
  ])
}

async function loadTrend() {
  try {
    const data = await adminApi.getTrend(days.value)
    renderChart(data)
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

function renderChart(data) {
  if (!trendChart.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(trendChart.value)
  }

  chartInstance.setOption({
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
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
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
  background: #fff;
  border-radius: 8px;
  padding: 16px;
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
}

.chart-container {
  height: 350px;
}

.rank-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1200px) {
  .rank-row {
    grid-template-columns: 1fr;
  }
}
</style>
