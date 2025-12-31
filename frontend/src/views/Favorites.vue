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
  background: #f5f6f7;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left .el-button {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
}

.title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.content-loading {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.not-logged-in,
.empty {
  background: #fff;
  border-radius: 8px;
  padding: 60px;
}

.favorites-header {
  margin-bottom: 20px;
}

.count {
  font-size: 14px;
  color: #909399;
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
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.favorite-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-main {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  cursor: pointer;
}

.tool-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.icon-placeholder {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 16px;
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
  margin-bottom: 8px;
}

.tool-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.favorited-time {
  font-size: 12px;
  color: #c0c4cc;
}

.card-actions {
  flex-shrink: 0;
  margin-left: 16px;
}

@media (max-width: 768px) {
  .favorite-card {
    flex-direction: column;
    align-items: stretch;
  }

  .card-actions {
    margin-left: 0;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
