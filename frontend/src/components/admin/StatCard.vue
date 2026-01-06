<template>
  <div class="stat-card" :class="colorClass">
    <div class="stat-card-bg"></div>
    <div class="stat-content">
      <div class="stat-icon-wrapper">
        <el-icon :size="24"><component :is="icon" /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value">
          <ICountUp
            :end-val="value"
            :options="countUpOptions"
          />
        </div>
        <div class="stat-label">{{ label }}</div>
        <div class="stat-trend" v-if="trend !== undefined && trend !== null">
          <span :class="trend >= 0 ? 'up' : 'down'">
            <el-icon>
              <CaretTop v-if="trend >= 0" />
              <CaretBottom v-else />
            </el-icon>
            {{ Math.abs(trend) }}%
          </span>
          <span class="trend-label">较昨日</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ICountUp from 'vue-countup-v3'
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  label: {
    type: String,
    required: true
  },
  icon: {
    type: [String, Object],
    required: true
  },
  colorClass: {
    type: String,
    default: 'purple'
  },
  trend: {
    type: Number,
    default: undefined
  }
})

const countUpOptions = computed(() => ({
  duration: 1.5,
  useEasing: true,
  useGrouping: true,
  separator: ',',
}))
</script>

<style scoped>
.stat-card {
  position: relative;
  padding: 24px;
  border-radius: 16px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

.stat-card-bg {
  position: absolute;
  top: 0;
  right: 0;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  opacity: 0.1;
  transform: translate(30%, -30%);
}

.stat-content {
  position: relative;
  display: flex;
  gap: 16px;
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
}

.stat-trend .up {
  display: flex;
  align-items: center;
  color: #10b981;
  font-weight: 500;
}

.stat-trend .down {
  display: flex;
  align-items: center;
  color: #ef4444;
  font-weight: 500;
}

.trend-label {
  color: #94a3b8;
  font-size: 12px;
}

/* 颜色主题 */
.stat-card.purple .stat-card-bg {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.stat-card.purple .stat-icon-wrapper {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-card.green .stat-card-bg {
  background: linear-gradient(135deg, #10b981, #059669);
}
.stat-card.green .stat-icon-wrapper {
  background: linear-gradient(135deg, #10b981, #059669);
}

.stat-card.orange .stat-card-bg {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}
.stat-card.orange .stat-icon-wrapper {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.stat-card.red .stat-card-bg {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}
.stat-card.red .stat-icon-wrapper {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.stat-card.cyan .stat-card-bg {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}
.stat-card.cyan .stat-icon-wrapper {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
}

.stat-card.violet .stat-card-bg {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}
.stat-card.violet .stat-icon-wrapper {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.stat-card.pink .stat-card-bg {
  background: linear-gradient(135deg, #ec4899, #db2777);
}
.stat-card.pink .stat-icon-wrapper {
  background: linear-gradient(135deg, #ec4899, #db2777);
}

.stat-card.rose .stat-card-bg {
  background: linear-gradient(135deg, #f43f5e, #e11d48);
}
.stat-card.rose .stat-icon-wrapper {
  background: linear-gradient(135deg, #f43f5e, #e11d48);
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
  }

  .stat-icon-wrapper {
    width: 48px;
    height: 48px;
  }

  .stat-value {
    font-size: 24px;
  }
}
</style>
