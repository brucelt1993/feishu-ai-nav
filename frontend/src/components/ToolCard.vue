<template>
  <div class="tool-card" :class="{ 'is-hot': isHot }" @click="handleClick">
    <!-- 热门标签 -->
    <div class="hot-badge" v-if="isHot">
      <el-icon><TrendCharts /></el-icon>
      <span>HOT</span>
    </div>

    <!-- 详情角标按钮 -->
    <button class="detail-badge" @click.stop="handleShowDetail" title="查看详情">
      <el-icon><InfoFilled /></el-icon>
    </button>

    <!-- 顶部区域：图标和信息 -->
    <div class="card-header">
      <div class="tool-icon" :style="iconStyle">
        <img v-if="tool.icon_url" :src="tool.icon_url" :alt="tool.name" />
        <span v-else class="icon-placeholder">{{ tool.name.charAt(0) }}</span>
      </div>
      <div class="tool-info">
        <div class="tool-name">
          {{ tool.name }}
          <el-tag v-if="isNew" size="small" type="success" class="new-tag">NEW</el-tag>
        </div>
        <div class="tool-desc" v-if="tool.description">{{ tool.description }}</div>
        <!-- 提供者信息 -->
        <div class="tool-provider" v-if="tool.provider">
          <el-icon><OfficeBuilding /></el-icon>
          <span>{{ tool.provider }}</span>
        </div>
        <!-- 热度指示器 -->
        <div class="heat-indicator" v-if="stats.like_count > 0">
          <div class="heat-bar">
            <div class="heat-fill" :style="{ width: heatPercentage + '%' }"></div>
          </div>
          <span class="heat-text">{{ stats.like_count }} 人推荐</span>
        </div>
      </div>
    </div>

    <!-- 交互栏 -->
    <div class="tool-actions" @click.stop>
      <button
        class="action-btn like-btn"
        :class="{ active: stats.is_liked }"
        @click="handleLike"
        :disabled="!canInteract"
        :title="canInteract ? (stats.is_liked ? '取消点赞' : '点赞') : '请先登录'"
      >
        <el-icon class="action-icon"><component :is="stats.is_liked ? 'StarFilled' : 'Star'" /></el-icon>
        <span class="action-text">{{ stats.like_count || '赞' }}</span>
      </button>
      <button
        class="action-btn fav-btn"
        :class="{ active: stats.is_favorited }"
        @click="handleFavorite"
        :disabled="!canInteract"
        :title="canInteract ? (stats.is_favorited ? '取消收藏' : '收藏') : '请先登录'"
      >
        <el-icon class="action-icon"><component :is="stats.is_favorited ? 'CollectionTag' : 'Collection'" /></el-icon>
        <span class="action-text">{{ stats.is_favorited ? '已收藏' : '收藏' }}</span>
      </button>
      <button
        class="action-btn feedback-btn"
        @click="handleFeedback"
        :disabled="!canInteract"
        :title="canInteract ? '反馈问题或建议' : '请先登录'"
      >
        <el-icon class="action-icon"><ChatLineSquare /></el-icon>
        <span class="action-text">反馈</span>
      </button>
    </div>

    <!-- 打开箭头 -->
    <div class="open-hint">
      <span>打开</span>
      <el-icon><ArrowRight /></el-icon>
    </div>

    <!-- 弹窗（使用 Teleport 避免定位问题） -->
    <Teleport to="body">
      <FeedbackDialog
        v-model="showFeedbackDialog"
        :tool="tool"
        @success="handleFeedbackSuccess"
      />
      <WantToolDialog
        v-model="showWantDialog"
        @success="handleWantSuccess"
      />
      <ToolDetailDialog
        v-model="showDetailDialog"
        :tool="tool"
        :category-color="categoryColor"
        @open="handleClick"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ArrowRight, Star, StarFilled, Collection, CollectionTag, ChatLineSquare, Promotion, TrendCharts, InfoFilled, OfficeBuilding } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { toolsApi } from '@/api'
import FeedbackDialog from './FeedbackDialog.vue'
import WantToolDialog from './WantToolDialog.vue'
import ToolDetailDialog from './ToolDetailDialog.vue'

const props = defineProps({
  tool: {
    type: Object,
    required: true
  },
  categoryColor: {
    type: String,
    default: '#667eea'
  },
  hotThreshold: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['click', 'statsChange'])

// 计算是否热门工具
const isHot = computed(() => stats.value.like_count >= props.hotThreshold)

// 计算是否新工具（7天内创建）
const isNew = computed(() => {
  if (!props.tool.created_at) return false
  const created = new Date(props.tool.created_at)
  const weekAgo = new Date()
  weekAgo.setDate(weekAgo.getDate() - 7)
  return created > weekAgo
})

// 热度百分比（用于热度条）
const heatPercentage = computed(() => {
  const count = stats.value.like_count || 0
  return Math.min(count * 10, 100)
})

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

const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn)
// 只有登录后才能交互
const canInteract = computed(() => isLoggedIn.value)
const showFeedbackDialog = ref(false)
const showWantDialog = ref(false)
const showDetailDialog = ref(false)

const stats = ref({
  like_count: 0,
  favorite_count: 0,
  is_liked: false,
  is_favorited: false
})

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    const data = await toolsApi.getStats(props.tool.id)
    stats.value = data
  } catch (e) {
    console.warn('获取工具统计失败:', e)
  }
}

function handleClick() {
  emit('click', props.tool)
}

async function handleLike() {
  if (!canInteract.value) return

  try {
    if (stats.value.is_liked) {
      await toolsApi.unlike(props.tool.id)
      stats.value.is_liked = false
      stats.value.like_count = Math.max(0, stats.value.like_count - 1)
    } else {
      await toolsApi.like(props.tool.id)
      stats.value.is_liked = true
      stats.value.like_count++
    }
    emit('statsChange', { toolId: props.tool.id, stats: stats.value })
  } catch (e) {
    console.error('点赞操作失败:', e)
  }
}

async function handleFavorite() {
  if (!canInteract.value) return

  try {
    if (stats.value.is_favorited) {
      await toolsApi.unfavorite(props.tool.id)
      stats.value.is_favorited = false
      stats.value.favorite_count = Math.max(0, stats.value.favorite_count - 1)
    } else {
      await toolsApi.favorite(props.tool.id)
      stats.value.is_favorited = true
      stats.value.favorite_count++
    }
    emit('statsChange', { toolId: props.tool.id, stats: stats.value })
  } catch (e) {
    console.error('收藏操作失败:', e)
  }
}

function handleFeedback() {
  if (!canInteract.value) return
  showFeedbackDialog.value = true
}

function handleShowDetail() {
  showDetailDialog.value = true
}

function handleFeedbackSuccess() {
  // 反馈成功后的回调
}

function handleWantSuccess() {
  // 想要工具提交成功后的回调
}
</script>

<style scoped>
.tool-card {
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
}

.tool-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-gradient);
  opacity: 0;
  transition: opacity 0.3s;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.2);
}

.tool-card:hover::before {
  opacity: 1;
}

.tool-card.is-hot {
  border-color: rgba(245, 108, 108, 0.3);
}

.tool-card.is-hot::before {
  background: linear-gradient(90deg, #f56c6c, #e6a23c);
}

/* 热门标签 */
.hot-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 12px;
  animation: pulse 2s infinite;
  z-index: 2;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 详情角标按钮 */
.detail-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(102, 126, 234, 0.1);
  color: var(--accent-color, #667eea);
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1;
}

.detail-badge:hover {
  background: var(--accent-color, #667eea);
  color: #fff;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.detail-badge .el-icon {
  font-size: 16px;
}

/* 热门时详情角标位置调整 */
.tool-card.is-hot .detail-badge {
  top: 48px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  gap: 16px;
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
  transition: transform 0.3s;
}

.tool-card:hover .tool-icon {
  transform: scale(1.05);
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

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-tag {
  font-size: 10px;
  padding: 0 6px;
  height: 18px;
  line-height: 18px;
}

.tool-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 6px;
}

/* 提供者信息 */
.tool-provider {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.tool-provider .el-icon {
  font-size: 14px;
  color: var(--accent-color);
}

/* 热度指示器 */
.heat-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.heat-bar {
  flex: 1;
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  max-width: 80px;
}

.heat-fill {
  height: 100%;
  background: var(--accent-gradient);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.heat-text {
  font-size: 11px;
  color: var(--text-muted);
}

/* 交互栏 */
.tool-actions {
  display: flex;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #e2e8f0);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 14px;
  border: 1.5px solid transparent;
  border-radius: 12px;
  background: var(--bg-tertiary, #f1f5f9);
  color: var(--text-secondary, #64748b);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.action-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.action-btn:hover:not(:disabled)::before {
  opacity: 1;
}

/* 点赞按钮 */
.like-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #f59e0b;
  color: #d97706;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
}

.like-btn.active {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #f59e0b;
  color: #d97706;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
}

/* 收藏按钮 */
.fav-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  border-color: #8b5cf6;
  color: #7c3aed;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);
}

.fav-btn.active {
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  border-color: #8b5cf6;
  color: #7c3aed;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2);
}

/* 反馈按钮 */
.feedback-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  border-color: #f87171;
  color: #dc2626;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(248, 113, 113, 0.25);
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
  filter: grayscale(0.3);
}

.action-icon {
  font-size: 18px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-btn:hover:not(:disabled) .action-icon {
  transform: scale(1.2) rotate(-5deg);
}

.like-btn.active .action-icon {
  color: #f59e0b;
  animation: likePopup 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 2px 4px rgba(245, 158, 11, 0.4));
}

@keyframes likePopup {
  0% { transform: scale(1) rotate(0); }
  25% { transform: scale(1.4) rotate(-15deg); }
  50% { transform: scale(0.9) rotate(10deg); }
  75% { transform: scale(1.15) rotate(-5deg); }
  100% { transform: scale(1) rotate(0); }
}

.fav-btn.active .action-icon {
  color: #8b5cf6;
  filter: drop-shadow(0 2px 4px rgba(139, 92, 246, 0.4));
}

.action-text {
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* 深色模式适配 */
:root.dark .like-btn:hover:not(:disabled),
:root.dark .like-btn.active {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.25) 100%);
  border-color: rgba(245, 158, 11, 0.5);
  color: #fbbf24;
}

:root.dark .fav-btn:hover:not(:disabled),
:root.dark .fav-btn.active {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(124, 58, 237, 0.25) 100%);
  border-color: rgba(139, 92, 246, 0.5);
  color: #a78bfa;
}

:root.dark .feedback-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.15) 0%, rgba(220, 38, 38, 0.2) 100%);
  border-color: rgba(248, 113, 113, 0.5);
  color: #fca5a5;
}

/* 深色模式详情角标 */
:root.dark .detail-badge {
  background: rgba(102, 126, 234, 0.2);
  color: #a5b4fc;
}

:root.dark .detail-badge:hover {
  background: rgba(102, 126, 234, 0.8);
  color: #fff;
}

/* 打开提示 */
.open-hint {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-muted);
  font-size: 12px;
  opacity: 0;
  transition: all 0.3s;
}

.tool-card:hover .open-hint {
  opacity: 1;
  color: var(--accent-color);
  right: 16px;
}

.open-hint .el-icon {
  font-size: 14px;
}

/* 移动端适配 */
@media (max-width: 640px) {
  .tool-card {
    padding: 16px;
  }

  .card-header {
    gap: 12px;
  }

  .tool-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }

  .tool-name {
    font-size: 15px;
  }

  .tool-actions {
    gap: 8px;
  }

  .action-btn {
    padding: 10px 8px;
    border-radius: 10px;
    flex-direction: column;
    gap: 4px;
  }

  .action-icon {
    font-size: 20px;
  }

  .action-text {
    font-size: 11px;
    font-weight: 500;
  }

  .open-hint {
    display: none;
  }
}
</style>
