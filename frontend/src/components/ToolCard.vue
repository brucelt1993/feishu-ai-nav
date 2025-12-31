<template>
  <div class="tool-card" @click="handleClick">
    <div class="tool-icon" :style="{ background: categoryColor }">
      <img v-if="tool.icon_url" :src="tool.icon_url" :alt="tool.name" />
      <span v-else class="icon-placeholder">{{ tool.name.charAt(0) }}</span>
    </div>
    <div class="tool-info">
      <div class="tool-name">{{ tool.name }}</div>
      <div class="tool-desc" v-if="tool.description">{{ tool.description }}</div>
    </div>
    <el-icon class="tool-arrow"><ArrowRight /></el-icon>

    <!-- 交互栏 -->
    <div class="tool-actions" @click.stop>
      <button
        class="action-btn"
        :class="{ active: stats.is_liked }"
        @click="handleLike"
        :disabled="!isLoggedIn"
        :title="isLoggedIn ? (stats.is_liked ? '取消点赞' : '点赞') : '请先登录'"
      >
        <el-icon><component :is="stats.is_liked ? 'StarFilled' : 'Star'" /></el-icon>
        <span>{{ stats.like_count }}</span>
      </button>
      <button
        class="action-btn"
        :class="{ active: stats.is_favorited }"
        @click="handleFavorite"
        :disabled="!isLoggedIn"
        :title="isLoggedIn ? (stats.is_favorited ? '取消收藏' : '收藏') : '请先登录'"
      >
        <el-icon><component :is="stats.is_favorited ? 'CollectionTag' : 'Collection'" /></el-icon>
        <span>{{ stats.is_favorited ? '已收藏' : '收藏' }}</span>
      </button>
      <button
        class="action-btn want-btn"
        @click="handleWant"
        :disabled="!isLoggedIn"
        :title="isLoggedIn ? '推荐新工具' : '请先登录'"
      >
        <el-icon><Promotion /></el-icon>
        <span>想要</span>
      </button>
      <button
        class="action-btn feedback-btn"
        @click="handleFeedback"
        :disabled="!isLoggedIn"
        :title="isLoggedIn ? '反馈问题或建议' : '请先登录'"
      >
        <el-icon><ChatLineSquare /></el-icon>
        <span>反馈</span>
      </button>
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
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ArrowRight, Star, StarFilled, Collection, CollectionTag, ChatLineSquare, Promotion } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { toolsApi } from '@/api'
import FeedbackDialog from './FeedbackDialog.vue'
import WantToolDialog from './WantToolDialog.vue'

const props = defineProps({
  tool: {
    type: Object,
    required: true
  },
  categoryColor: {
    type: String,
    default: '#667eea'
  }
})

const emit = defineEmits(['click', 'statsChange'])

const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn)
const showFeedbackDialog = ref(false)
const showWantDialog = ref(false)

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
  if (!isLoggedIn.value) return

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
  if (!isLoggedIn.value) return

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
  if (!isLoggedIn.value) return
  showFeedbackDialog.value = true
}

function handleWant() {
  if (!isLoggedIn.value) return
  showWantDialog.value = true
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
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
  position: relative;
}

.tool-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: transparent;
}

.tool-card > .tool-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #c0c4cc;
  font-size: 16px;
}

.tool-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-bottom: 12px;
}

.tool-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.icon-placeholder {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.tool-info {
  flex: 1;
  min-width: 0;
  margin-bottom: 12px;
}

.tool-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-actions {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 16px;
  background: #f5f7fa;
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: #ecf5ff;
  color: #409eff;
}

.action-btn.active {
  background: #ecf5ff;
  color: #409eff;
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.action-btn .el-icon {
  font-size: 16px;
}

.want-btn:hover:not(:disabled) {
  background: #fdf6ec;
  color: #e6a23c;
}

.feedback-btn:hover:not(:disabled) {
  background: #fef0f0;
  color: #f56c6c;
}
</style>
