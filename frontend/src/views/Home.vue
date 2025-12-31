<template>
  <div class="home">
    <!-- 顶部栏 -->
    <header class="header">
      <h1 class="title">🤖 AI工具导航</h1>
      <div class="header-right">
        <button
          class="want-tool-btn"
          v-if="userStore.isLoggedIn"
          @click="showWantDialog = true"
        >
          <el-icon><Plus /></el-icon>
          <span>想要工具</span>
        </button>
        <router-link to="/favorites" class="favorites-link" v-if="userStore.isLoggedIn">
          <el-icon><Collection /></el-icon>
          <span>收藏</span>
        </router-link>
        <div class="user-info" v-if="userStore.isLoggedIn">
          <el-avatar :src="userStore.userAvatar" :size="32">
            {{ userStore.userName.charAt(0) }}
          </el-avatar>
          <span class="user-name">{{ userStore.userName }}</span>
        </div>
        <el-button v-else type="primary" size="small" @click="handleLogin">
          登录
        </el-button>
      </div>
    </header>

    <!-- 模式切换栏 -->
    <div class="mode-bar">
      <div class="mode-tabs">
        <button
          class="mode-tab"
          :class="{ active: currentMode === 'category' }"
          @click="setMode('category')"
        >
          <el-icon><Menu /></el-icon>
          <span>目录</span>
        </button>
        <button
          class="mode-tab"
          :class="{ active: currentMode === 'global' }"
          @click="setMode('global')"
        >
          <el-icon><Grid /></el-icon>
          <span>全局</span>
        </button>
      </div>

      <!-- 搜索框（目录/全局/搜索模式都显示） -->
      <div class="search-box">
        <el-input
          v-model="searchInput"
          placeholder="搜索工具名称或描述..."
          :prefix-icon="Search"
          clearable
          @input="handleSearchInput"
          @clear="handleSearchClear"
          @keyup.enter="handleSearchEnter"
        />
      </div>

      <!-- 全局模式排序 -->
      <div class="sort-box" v-if="currentMode === 'global'">
        <span class="sort-label">排序：</span>
        <el-select v-model="sortBy" size="small" @change="loadGlobalTools">
          <el-option label="默认" value="default" />
          <el-option label="最热" value="hot" />
          <el-option label="最新" value="recent" />
          <el-option label="名称" value="name" />
        </el-select>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="main-container" :class="{ 'no-sidebar': currentMode !== 'category' }">
      <!-- 左侧分类菜单（仅目录模式） -->
      <aside class="sidebar" v-if="currentMode === 'category'">
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
        <!-- 未登录且不允许匿名访问时显示登录提示 -->
        <div v-if="!canViewTools" class="login-prompt">
          <el-empty description="请先登录后查看工具列表">
            <template #image>
              <el-icon :size="64" color="#c0c4cc"><User /></el-icon>
            </template>
            <el-button type="primary" @click="handleLogin">立即登录</el-button>
          </el-empty>
        </div>

        <div v-else-if="loading" class="content-loading">
          <el-skeleton :rows="6" animated />
        </div>

        <template v-else>
          <!-- 目录模式 -->
          <template v-if="currentMode === 'category'">
            <div class="content-header">
              <h2 class="category-title">{{ currentCategoryName }}</h2>
              <span class="tool-total">共 {{ currentTools.length }} 个工具</span>
            </div>

            <div v-if="currentTools.length === 0" class="empty">
              <el-empty description="该分类暂无工具" />
            </div>

            <div v-else class="tool-grid">
              <ToolCard
                v-for="tool in currentTools"
                :key="tool.id"
                :tool="tool"
                :category-color="currentCategoryColor"
                @click="handleToolClick"
              />
            </div>
          </template>

          <!-- 全局模式 -->
          <template v-else-if="currentMode === 'global'">
            <div class="content-header">
              <h2 class="category-title">全部工具</h2>
              <span class="tool-total">共 {{ globalTools.length }} 个工具</span>
            </div>

            <div v-if="globalTools.length === 0" class="empty">
              <el-empty description="暂无工具" />
            </div>

            <div v-else class="tool-grid">
              <ToolCard
                v-for="tool in globalTools"
                :key="tool.id"
                :tool="tool"
                @click="handleToolClick"
              />
            </div>
          </template>

          <!-- 搜索模式 -->
          <template v-else-if="currentMode === 'search'">
            <div class="content-header">
              <h2 class="category-title">
                {{ searchKeyword ? `搜索: ${searchKeyword}` : '请输入搜索关键词' }}
              </h2>
              <span class="tool-total" v-if="searchKeyword">
                找到 {{ searchResults.length }} 个工具
              </span>
            </div>

            <div v-if="!searchKeyword" class="empty">
              <el-empty description="输入关键词搜索工具">
                <template #image>
                  <el-icon :size="64" color="#c0c4cc"><Search /></el-icon>
                </template>
              </el-empty>
            </div>

            <div v-else-if="searchResults.length === 0" class="empty">
              <el-empty :description="`未找到包含 '${searchKeyword}' 的工具`" />
            </div>

            <div v-else class="tool-grid">
              <ToolCard
                v-for="tool in searchResults"
                :key="tool.id"
                :tool="tool"
                @click="handleToolClick"
              />
            </div>
          </template>
        </template>
      </main>
    </div>

    <!-- 想要工具弹窗 -->
    <WantToolDialog v-model="showWantDialog" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Collection, Plus, Menu, Grid, Search, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { categoriesApi, toolsApi } from '@/api'
import { initFeishuSDK, feishuLogin, openInFeishu, isInFeishu } from '@/utils/feishu'
import { useNavMode } from '@/composables/useNavMode'
import ToolCard from '@/components/ToolCard.vue'
import WantToolDialog from '@/components/WantToolDialog.vue'

const userStore = useUserStore()
const { currentMode, searchKeyword, sortBy, setMode, setSearchKeyword, clearSearch } = useNavMode()

// 是否允许匿名访问（需要重启 Vite 才能生效）
const allowAnonymous = import.meta.env.VITE_ALLOW_ANONYMOUS === 'true'
const canViewTools = computed(() => allowAnonymous || userStore.isLoggedIn)

const categories = ref([])
const loading = ref(true)
const activeCategory = ref('')
const showWantDialog = ref(false)

// 全局模式数据
const globalTools = ref([])

// 搜索模式数据
const searchInput = ref('')
const searchResults = ref([])
let searchTimeout = null

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

// 监听模式切换
watch(currentMode, async (mode) => {
  if (mode === 'global') {
    await loadGlobalTools()
  } else if (mode === 'search') {
    searchInput.value = searchKeyword.value
  }
})

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

async function loadGlobalTools() {
  try {
    loading.value = true
    globalTools.value = await toolsApi.getList({
      mode: 'all',
      sort: sortBy.value
    })
  } catch (error) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleSearchInput(value) {
  // 防抖处理
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    doSearch(value)
  }, 300)
}

function handleSearchClear() {
  clearSearch()
  searchResults.value = []
  // 如果当前在搜索模式，清空后不切换模式
}

function handleSearchEnter() {
  // 回车时如果有内容，自动切换到搜索模式
  if (searchInput.value?.trim()) {
    setMode('search')
    doSearch(searchInput.value)
  }
}

async function doSearch(keyword) {
  keyword = keyword?.trim() || ''
  setSearchKeyword(keyword)

  if (!keyword) {
    searchResults.value = []
    return
  }

  // 如果有搜索内容，自动切换到搜索模式显示结果
  if (currentMode.value !== 'search') {
    setMode('search')
  }

  try {
    searchResults.value = await toolsApi.getList({ keyword })
  } catch (error) {
    console.error('搜索失败:', error)
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

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.favorites-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  transition: all 0.2s;
}

.favorites-link:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.want-tool-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.want-tool-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 14px;
}

/* 模式切换栏 */
.mode-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.mode-tabs {
  display: flex;
  gap: 4px;
  background: #f5f7fa;
  padding: 4px;
  border-radius: 8px;
}

.mode-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  transition: all 0.2s;
}

.mode-tab:hover {
  color: #409eff;
}

.mode-tab.active {
  background: #fff;
  color: #409eff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.sort-box {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.sort-label {
  font-size: 14px;
  color: #909399;
}

/* 主体区域 */
.main-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.main-container.no-sidebar {
  /* 无侧边栏时的样式 */
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

.login-prompt {
  background: #fff;
  border-radius: 8px;
  padding: 80px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }

  .mode-bar {
    flex-wrap: wrap;
  }

  .search-box {
    width: 100%;
    max-width: none;
    order: 10;
    margin-top: 8px;
  }

  .tool-grid {
    grid-template-columns: 1fr;
  }
}
</style>
