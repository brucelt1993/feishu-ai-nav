<template>
  <div class="home">
    <!-- 顶部栏 -->
    <header class="header">
      <h1 class="title">🤖 AI工具导航</h1>
      <div class="user-info" v-if="userStore.isLoggedIn">
        <el-avatar :src="userStore.userAvatar" :size="32">
          {{ userStore.userName.charAt(0) }}
        </el-avatar>
        <span class="user-name">{{ userStore.userName }}</span>
      </div>
      <el-button v-else type="primary" size="small" @click="handleLogin">
        登录
      </el-button>
    </header>

    <!-- 工具列表 -->
    <main class="main">
      <div v-if="loading" class="loading">
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="tools.length === 0" class="empty">
        <el-empty description="暂无工具" />
      </div>

      <div v-else class="tool-grid">
        <div
          v-for="tool in tools"
          :key="tool.id"
          class="tool-card"
          @click="handleToolClick(tool)"
        >
          <div class="tool-icon">
            <img v-if="tool.icon_url" :src="tool.icon_url" :alt="tool.name" />
            <span v-else class="icon-placeholder">{{ tool.name.charAt(0) }}</span>
          </div>
          <div class="tool-name">{{ tool.name }}</div>
          <div class="tool-desc" v-if="tool.description">{{ tool.description }}</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { toolsApi } from '@/api'
import { feishuLogin, openInFeishu, isInFeishu } from '@/utils/feishu'

const userStore = useUserStore()
const tools = ref([])
const loading = ref(true)

onMounted(async () => {
  await loadTools()

  // 如果在飞书环境且未登录，自动尝试登录
  if (isInFeishu() && !userStore.isLoggedIn) {
    try {
      await feishuLogin()
    } catch (e) {
      console.warn('自动登录失败:', e)
    }
  }
})

async function loadTools() {
  try {
    loading.value = true
    tools.value = await toolsApi.getList()
  } catch (error) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  if (!isInFeishu()) {
    ElMessage.warning('请在飞书中打开此页面')
    return
  }

  try {
    await feishuLogin()
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error('登录失败')
  }
}

async function handleToolClick(tool) {
  try {
    // 记录点击
    await toolsApi.recordClick(tool.id)
  } catch (e) {
    console.warn('记录点击失败:', e)
  }

  // 跳转到工具URL
  openInFeishu(tool.target_url)
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  color: #fff;
  font-size: 14px;
}

.main {
  padding: 20px;
}

.loading,
.empty {
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  margin: 20px 0;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.tool-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.tool-card:active {
  transform: scale(0.98);
}

.tool-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.tool-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.icon-placeholder {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.tool-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-desc {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (min-width: 768px) {
  .tool-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 1024px) {
  .tool-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}
</style>
