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

    <!-- 主体区域 -->
    <div class="main-container">
      <!-- 左侧分类菜单 -->
      <aside class="sidebar">
        <div v-if="loading" class="sidebar-loading">
          <el-skeleton :rows="8" animated />
        </div>
        <el-menu
          v-else
          :default-active="activeCategory"
          class="category-menu"
          @select="handleCategorySelect"
        >
          <template v-for="cat in categories" :key="cat.id">
            <!-- 有子分类 -->
            <el-sub-menu v-if="cat.children?.length" :index="String(cat.id)">
              <template #title>
                <span class="cat-icon" :style="{ background: cat.color || '#667eea' }">
                  {{ cat.name.charAt(0) }}
                </span>
                <span>{{ cat.name }}</span>
              </template>
              <el-menu-item
                v-for="child in cat.children"
                :key="child.id"
                :index="String(child.id)"
              >
                {{ child.name }}
                <span class="tool-count">{{ child.tools?.length || 0 }}</span>
              </el-menu-item>
            </el-sub-menu>

            <!-- 无子分类 -->
            <el-menu-item v-else :index="String(cat.id)">
              <span class="cat-icon" :style="{ background: cat.color || '#667eea' }">
                {{ cat.name.charAt(0) }}
              </span>
              <span>{{ cat.name }}</span>
              <span class="tool-count">{{ cat.tools?.length || 0 }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </aside>

      <!-- 右侧工具列表 -->
      <main class="content">
        <div v-if="loading" class="content-loading">
          <el-skeleton :rows="6" animated />
        </div>

        <template v-else>
          <div class="content-header">
            <h2 class="category-title">{{ currentCategoryName }}</h2>
            <span class="tool-total">共 {{ currentTools.length }} 个工具</span>
          </div>

          <div v-if="currentTools.length === 0" class="empty">
            <el-empty description="该分类暂无工具" />
          </div>

          <div v-else class="tool-grid">
            <div
              v-for="tool in currentTools"
              :key="tool.id"
              class="tool-card"
              @click="handleToolClick(tool)"
            >
              <div class="tool-icon" :style="{ background: currentCategoryColor }">
                <img v-if="tool.icon_url" :src="tool.icon_url" :alt="tool.name" />
                <span v-else class="icon-placeholder">{{ tool.name.charAt(0) }}</span>
              </div>
              <div class="tool-info">
                <div class="tool-name">{{ tool.name }}</div>
                <div class="tool-desc" v-if="tool.description">{{ tool.description }}</div>
              </div>
              <el-icon class="tool-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { categoriesApi, toolsApi } from '@/api'
import { initFeishuSDK, feishuLogin, openInFeishu, isInFeishu } from '@/utils/feishu'

const userStore = useUserStore()
const categories = ref([])
const loading = ref(true)
const activeCategory = ref('')

// 当前选中的分类
const currentCategory = computed(() => {
  if (!activeCategory.value) return null

  for (const cat of categories.value) {
    if (String(cat.id) === activeCategory.value) return cat
    for (const child of cat.children || []) {
      if (String(child.id) === activeCategory.value) return child
    }
  }
  return null
})

const currentCategoryName = computed(() => currentCategory.value?.name || '全部工具')
const currentCategoryColor = computed(() => currentCategory.value?.color || '#667eea')
const currentTools = computed(() => currentCategory.value?.tools || [])

onMounted(async () => {
  await loadCategories()

  // 飞书环境自动登录
  console.log('检测飞书环境:', isInFeishu(), 'UA:', navigator.userAgent)

  if (isInFeishu() && !userStore.isLoggedIn) {
    try {
      console.log('开始初始化飞书SDK...')
      const sdkReady = await initFeishuSDK()
      console.log('SDK初始化结果:', sdkReady)

      if (sdkReady) {
        console.log('开始飞书登录...')
        await feishuLogin()
        console.info('飞书自动登录成功')
      }
    } catch (e) {
      console.error('自动登录失败:', e)
    }
  }
})

async function loadCategories() {
  try {
    loading.value = true
    categories.value = await categoriesApi.getTree()

    // 默认选中第一个有工具的分类
    if (categories.value.length) {
      const first = categories.value[0]
      if (first.children?.length) {
        activeCategory.value = String(first.children[0].id)
      } else {
        activeCategory.value = String(first.id)
      }
    }
  } catch (error) {
    console.error('加载分类失败:', error)
    ElMessage.error('加载分类失败')
  } finally {
    loading.value = false
  }
}

function handleCategorySelect(index) {
  activeCategory.value = index
}

async function handleLogin() {
  if (!isInFeishu()) {
    ElMessage.warning('请在飞书中打开此页面')
    return
  }

  try {
    // 确保SDK已初始化
    if (!window.__FEISHU_APP_ID__) {
      await initFeishuSDK()
    }
    await feishuLogin()
    ElMessage.success('登录成功')
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error('登录失败')
  }
}

async function handleToolClick(tool) {
  try {
    await toolsApi.recordClick(tool.id)
  } catch (e) {
    console.warn('记录点击失败:', e)
  }

  openInFeishu(tool.target_url)
}
</script>

<style scoped>
.home {
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

.title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 14px;
}

.main-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #ebeef5;
  overflow-y: auto;
}

.sidebar-loading {
  padding: 20px;
}

.category-menu {
  border-right: none;
}

.cat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  margin-right: 8px;
}

.tool-count {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content-loading {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.category-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.tool-total {
  font-size: 14px;
  color: #909399;
}

.empty {
  background: #fff;
  border-radius: 8px;
  padding: 60px;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.tool-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
}

.tool-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: transparent;
}

.tool-icon {
  width: 48px;
  height: 48px;
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
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.tool-info {
  flex: 1;
  min-width: 0;
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

.tool-arrow {
  color: #c0c4cc;
  font-size: 16px;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }

  .tool-grid {
    grid-template-columns: 1fr;
  }
}
</style>
