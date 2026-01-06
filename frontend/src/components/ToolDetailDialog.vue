<template>
  <el-dialog
    v-model="visible"
    :title="tool?.name || '工具详情'"
    width="480px"
    class="tool-detail-dialog"
    :close-on-click-modal="true"
    destroy-on-close
  >
    <div class="tool-detail" v-if="tool">
      <!-- 头部信息 -->
      <div class="detail-header">
        <div class="tool-icon" :style="iconStyle">
          <img v-if="tool.icon_url" :src="tool.icon_url" :alt="tool.name" />
          <span v-else class="icon-placeholder">{{ tool.name.charAt(0) }}</span>
        </div>
        <div class="tool-meta">
          <h3 class="tool-name">{{ tool.name }}</h3>
          <div class="tool-provider" v-if="tool.provider">
            <el-icon><OfficeBuilding /></el-icon>
            <span>{{ tool.provider }}</span>
          </div>
        </div>
      </div>

      <!-- 描述信息 -->
      <div class="detail-section">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          <span>工具介绍</span>
        </div>
        <div class="section-content">
          <p class="tool-desc">{{ tool.description || '暂无描述' }}</p>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button type="primary" @click="handleOpen">
          <el-icon><Link /></el-icon>
          <span>打开工具</span>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { OfficeBuilding, Document, Link } from '@element-plus/icons-vue'

const props = defineProps({
  tool: {
    type: Object,
    default: null
  },
  categoryColor: {
    type: String,
    default: '#667eea'
  }
})

const emit = defineEmits(['open'])

const visible = defineModel({ type: Boolean, default: false })

// 动态图标样式
const iconStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.categoryColor} 0%, ${adjustColor(props.categoryColor, -20)} 100%)`
}))

// 颜色调整函数
function adjustColor(color, amount) {
  const hex = color.replace('#', '')
  const num = parseInt(hex, 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount))
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount))
  return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`
}

function handleOpen() {
  emit('open', props.tool)
  visible.value = false
}
</script>

<style scoped>
.tool-detail-dialog :deep(.el-dialog__header) {
  padding: 16px 20px;
  margin: 0;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.tool-detail-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

.tool-detail-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.tool-detail {
  padding: 20px;
}

/* 头部信息 */
.detail-header {
  display: flex;
  gap: 14px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
  margin-bottom: 16px;
}

.tool-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tool-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 14px;
}

.icon-placeholder {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tool-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tool-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin: 0 0 6px 0;
}

.tool-provider {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary, #64748b);
}

.tool-provider .el-icon {
  font-size: 15px;
  color: var(--accent-color, #667eea);
}

/* 详情区块 */
.detail-section {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #64748b);
  margin-bottom: 10px;
}

.section-title .el-icon {
  font-size: 15px;
  color: var(--accent-color, #667eea);
}

.section-content {
  padding-left: 21px;
}

.tool-desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary, #1e293b);
  white-space: pre-wrap;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button {
  min-width: 90px;
}
</style>
