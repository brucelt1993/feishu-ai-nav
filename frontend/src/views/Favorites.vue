<template>
  <div class="favorites-page">
    <!-- 顶部栏 -->
    <header class="header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" circle @click="goBack" />
        <h1 class="title">我的收藏</h1>
      </div>
      <div class="user-info" v-if="userStore.isLoggedIn">
        <el-avatar :src="userStore.userAvatar" :size="32">
          {{ userStore.userName.charAt(0) }}
        </el-avatar>
      </div>
    </header>

    <!-- 内容区域 -->
    <main class="content">
      <div v-if="loading" class="content-loading">
        <el-skeleton :rows="6" animated />
      </div>

      <template v-else>
        <div v-if="!userStore.isLoggedIn" class="not-logged-in">
          <el-empty description="请先登录查看收藏">
            <el-button type="primary" @click="goHome">返回首页</el-button>
          </el-empty>
        </div>

        <div v-else-if="favorites.length === 0" class="empty">
          <el-empty description="还没有收藏任何工具">
            <el-button type="primary" @click="goHome">去收藏</el-button>
          </el-empty>
        </div>

        <div v-else>
          <div class="favorites-header">
            <span class="count">共 {{ favorites.length }} 个收藏</span>
          </div>
          <div class="tool-grid">
            <div
              v-for="item in favorites"
              :key="item.id"
              class="favorite-card"
            >
              <div class="card-main" @click="handleToolClick(item)">
                <div class="tool-icon" :style="{ background: item.category_color || '#667eea' }">
                  <img v-if="item.icon_url" :src="item.icon_url" :alt="item.name" />
                  <span v-else class="icon-placeholder">{{ item.name.charAt(0) }}</span>
                </div>
                <div class="tool-info">
                  <div class="tool-name">{{ item.name }}</div>
                  <div class="tool-desc" v-if="item.description">{{ item.description }}</div>
                  <div class="tool-meta">
                    <el-tag size="small" v-if="item.category_name">{{ item.category_name }}</el-tag>
                    <span class="favorited-time">收藏于 {{ formatTime(item.favorited_at) }}</span>
                  </div>
                </div>
              </div>
              <div class="card-actions">
                <el-button
                  type="danger"
                  size="small"
                  plain
                  @click="handleRemoveFavorite(item)"
                >
                  取消收藏
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { userApi, toolsApi } from '@/api'
import { openInFeishu } from '@/utils/feishu'

const router = useRouter()
const userStore = useUserStore()
const favorites = ref([])
const loading = ref(true)

onMounted(async () => {
  if (userStore.isLoggedIn) {
    await loadFavorites()
  } else {
    loading.value = false
  }
})

async function loadFavorites() {
  try {
    loading.value = true
    const res = await userApi.getFavorites()
    favorites.value = res.items || []
  } catch (error) {
    console.error('加载收藏失败:', error)
    ElMessage.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

function goHome() {
  router.push('/')
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

async function handleToolClick(item) {
  try {
    await toolsApi.recordClick(item.id)
  } catch (e) {
    console.warn('记录点击失败:', e)
  }
  openInFeishu(item.target_url)
}

async function handleRemoveFavorite(item) {
  try {
    await ElMessageBox.confirm(
      `确定取消收藏"${item.name}"吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await toolsApi.unfavorite(item.id)
    favorites.value = favorites.value.filter(f => f.id !== item.id)
    ElMessage.success('已取消收藏')
  } catch (e) {
    if (e !== 'cancel') {
      console.error('取消收藏失败:', e)
      ElMessage.error('操作失败')
    }
  }
}
</script>

<style scoped>
.favorites-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left .el-button {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
}

.header-left .el-button:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateX(-2px);
}

.title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.5px;
}

.content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.content-loading {
  background: var(--bg-secondary);
  padding: 24px;
  border-radius: 16px;
  box-shadow: var(--shadow-md);
}

.not-logged-in,
.empty {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 80px 40px;
  box-shadow: var(--shadow-md);
  text-align: center;
}

.favorites-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--bg-tertiary);
}

.count {
  font-size: 14px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 6px 14px;
  border-radius: 20px;
}

.tool-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.favorite-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid var(--border-color);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.favorite-card::before {
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

.favorite-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.2);
}

.favorite-card:hover::before {
  opacity: 1;
}

.card-main {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
  cursor: pointer;
}

.tool-icon {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.favorite-card:hover .tool-icon {
  transform: scale(1.05);
}

.tool-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 14px;
}

.icon-placeholder {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.tool-desc {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 10px;
  line-height: 1.5;
}

.tool-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.favorited-time {
  font-size: 12px;
  color: var(--text-muted);
}

.card-actions {
  flex-shrink: 0;
  margin-left: 20px;
}

.card-actions .el-button {
  border-radius: 10px;
  padding: 10px 16px;
  font-weight: 500;
  transition: all 0.25s;
}

.card-actions .el-button:hover {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }

  .title {
    font-size: 18px;
  }

  .content {
    padding: 16px;
  }

  .favorite-card {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .card-main {
    gap: 16px;
  }

  .tool-icon {
    width: 48px;
    height: 48px;
  }

  .card-actions {
    margin-left: 0;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: flex-end;
  }
}
</style>
