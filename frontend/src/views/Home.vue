<template>
  <div class="home">
    <!-- 顶部栏 -->
    <header class="header">
      <h1 class="title">🤖 AI工具导航</h1>
      <div class="header-right">
        <!-- 主题切换 -->
        <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换亮色模式' : '切换深色模式'">
          <el-icon :size="18"><component :is="isDark ? Sunny : Moon" /></el-icon>
        </button>
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
          <span>分类浏览</span>
        </button>
        <button
          class="mode-tab"
          :class="{ active: currentMode === 'global' }"
          @click="setMode('global')"
        >
          <el-icon><Grid /></el-icon>
          <span>全部工具</span>
        </button>
      </div>

      <!-- 搜索框（目录/全局/搜索模式都显示） -->
      <div class="search-box">
        <el-popover
          :visible="showHotwords && (hotwords.length > 0 || searchHistory.length > 0)"
          placement="bottom-start"
          :width="400"
          trigger="manual"
          :show-arrow="false"
        >
          <template #reference>
            <el-input
              v-model="searchInput"
              placeholder="搜索工具名称或描述..."
              :prefix-icon="Search"
              clearable
              @focus="showHotwords = true"
              @blur="handleSearchBlur"
              @input="handleSearchInput"
              @clear="handleSearchClear"
              @keyup.enter="handleSearchEnter"
            />
          </template>
          <div class="search-panel">
            <!-- 搜索历史 -->
            <div class="history-section" v-if="searchHistory.length > 0">
              <div class="section-header">
                <div class="section-title">
                  <el-icon><Clock /></el-icon>
                  <span>搜索历史</span>
                </div>
                <button class="clear-btn" @mousedown.prevent="handleClearHistory">清空</button>
              </div>
              <div class="history-list">
                <div
                  v-for="item in searchHistory.slice(0, 8)"
                  :key="item.id"
                  class="history-item"
                >
                  <button class="history-text" @mousedown.prevent="handleHistoryClick(item.keyword)">
                    {{ item.keyword }}
                  </button>
                  <button class="delete-btn" @mousedown.prevent="handleDeleteHistory(item.id)">
                    <el-icon><Close /></el-icon>
                  </button>
                </div>
              </div>
            </div>

            <!-- 热门搜索 -->
            <div class="hotwords-section" v-if="hotwords.length > 0">
              <div class="section-header">
                <div class="section-title">
                  <el-icon><TrendCharts /></el-icon>
                  <span>热门搜索</span>
                </div>
              </div>
              <div class="hotwords-list">
                <button
                  v-for="(word, index) in hotwords"
                  :key="word"
                  class="hotword-tag"
                  :class="{ 'is-top': index < 3 }"
                  @mousedown.prevent="handleHotwordClick(word)"
                >
                  <span class="hotword-rank">{{ index + 1 }}</span>
                  <span class="hotword-text">{{ word }}</span>
                </button>
              </div>
            </div>
          </div>
        </el-popover>
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

    <!-- 标签筛选栏（全局模式显示） -->
    <div class="tag-filter-bar" v-if="currentMode === 'global' && allTags.length > 0">
      <div class="tag-filter-label">
        <el-icon><PriceTag /></el-icon>
        <span>标签筛选</span>
      </div>
      <div class="tag-filter-list">
        <button
          v-for="tag in allTags"
          :key="tag.id"
          class="tag-filter-item"
          :class="{ active: selectedTagId === tag.id }"
          :style="selectedTagId === tag.id ? { background: tag.color, borderColor: tag.color, color: '#fff' } : {}"
          @click="handleTagClick(tag.id)"
        >
          <span class="tag-dot" :style="{ background: tag.color }" v-if="selectedTagId !== tag.id"></span>
          {{ tag.name }}
        </button>
        <button
          v-if="selectedTagId"
          class="tag-clear-btn"
          @click="selectedTagId = null; loadGlobalTools()"
        >
          <el-icon><Close /></el-icon>
          清除筛选
        </button>
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
                <div class="cat-item-wrapper">
                  <span class="cat-icon" :style="{ background: cat.color || '#667eea' }">
                    {{ cat.name.charAt(0) }}
                  </span>
                  <span class="cat-name">{{ cat.name }}</span>
                </div>
              </template>
              <el-menu-item
                v-for="child in cat.children"
                :key="child.id"
                :index="String(child.id)"
                class="child-menu-item"
              >
                <div class="child-item-wrapper">
                  <span class="child-name">{{ child.name }}</span>
                  <span class="tool-badge" v-if="child.tools?.length">{{ child.tools.length }}</span>
                </div>
              </el-menu-item>
            </el-sub-menu>

            <!-- 无子分类 -->
            <el-menu-item v-else :index="String(cat.id)">
              <div class="cat-item-wrapper">
                <span class="cat-icon" :style="{ background: cat.color || '#667eea' }">
                  {{ cat.name.charAt(0) }}
                </span>
                <span class="cat-name">{{ cat.name }}</span>
                <span class="tool-badge" v-if="cat.tools?.length">{{ cat.tools.length }}</span>
              </div>
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

    <!-- 快捷键帮助按钮 -->
    <button class="shortcuts-fab" @click="showShortcutsHint = true" title="快捷键帮助 (?)">
      <el-icon><QuestionFilled /></el-icon>
    </button>

    <!-- 快捷键帮助弹窗 -->
    <Teleport to="body">
      <div class="shortcuts-modal" v-if="showShortcutsHint" @click.self="showShortcutsHint = false">
        <div class="shortcuts-content">
          <div class="shortcuts-header">
            <h3>键盘快捷键</h3>
            <button class="close-btn" @click="showShortcutsHint = false">
              <span>×</span>
            </button>
          </div>
          <div class="shortcuts-list">
            <div v-for="shortcut in shortcuts" :key="shortcut.desc" class="shortcut-item">
              <div class="shortcut-keys">
                <kbd v-for="key in shortcut.keys" :key="key">{{ key }}</kbd>
              </div>
              <span class="shortcut-desc">{{ shortcut.desc }}</span>
            </div>
          </div>
          <div class="shortcuts-footer">
            按 <kbd>?</kbd> 切换此帮助
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Collection, Plus, Menu, Grid, Search, User, Sunny, Moon, TrendCharts, QuestionFilled, Clock, Close, PriceTag } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { categoriesApi, toolsApi } from '@/api'
import { openInFeishu, isInFeishu } from '@/utils/feishu'
import { useNavMode } from '@/composables/useNavMode'
import { useTheme } from '@/composables/useTheme'
import { useKeyboardNav } from '@/composables/useKeyboardNav'
import { useSearchHistory } from '@/composables/useSearchHistory'
import ToolCard from '@/components/ToolCard.vue'
import WantToolDialog from '@/components/WantToolDialog.vue'

const router = useRouter()
const userStore = useUserStore()

// 是否允许匿名访问（从环境变量读取）
const allowAnonymous = import.meta.env.VITE_ALLOW_ANONYMOUS === 'true'
// 是否可以查看工具列表（已登录 或 允许匿名访问）
const canViewTools = computed(() => allowAnonymous || userStore.isLoggedIn)
const { currentMode, searchKeyword, sortBy, setMode, setSearchKeyword, clearSearch } = useNavMode()
const { isDark, toggleTheme } = useTheme()
const { searchHistory, fetchHistory, addHistory, deleteHistory, clearHistory } = useSearchHistory()

// 搜索框ref
const searchInputRef = ref(null)

// 快捷键导航
const { showShortcutsHint, shortcuts } = useKeyboardNav({
  onSearch: () => {
    document.querySelector('.search-box input')?.focus()
  },
  onToggleTheme: toggleTheme,
  onGoHome: () => router.push('/'),
  onGoFavorites: () => {
    if (userStore.isLoggedIn) {
      router.push('/favorites')
    } else {
      ElMessage.warning('请先登录')
    }
  },
  onEscape: () => {
    showHotwords.value = false
    clearSearch()
    searchInput.value = ''
  }
})

// 搜索热词
const hotwords = ref([])
const showHotwords = ref(false)

const categories = ref([])
const loading = ref(true)
const activeCategory = ref('')
const showWantDialog = ref(false)

// 全局模式数据
const globalTools = ref([])

// 标签筛选
const allTags = ref([])
const selectedTagId = ref(null)

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
  // 并行加载数据
  const dataPromises = [
    loadCategories(),
    loadTags(),
  ]

  // 热词和历史不影响主体，静默加载
  loadHotwords()
  if (userStore.isLoggedIn) {
    fetchHistory()
  }

  // 等待核心数据加载完成
  await Promise.all(dataPromises)

  // 如果当前是全局模式，加载全部工具
  if (currentMode.value === 'global') {
    await loadGlobalTools()
  }
})

// 清理搜索超时
onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})

// 加载标签
async function loadTags() {
  try {
    allTags.value = await toolsApi.getTags()
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

// 处理标签点击筛选
function handleTagClick(tagId) {
  if (selectedTagId.value === tagId) {
    selectedTagId.value = null // 取消选中
  } else {
    selectedTagId.value = tagId
  }
  // 在全局模式下重新加载工具
  if (currentMode.value === 'global') {
    loadGlobalTools()
  }
}

// 加载热门搜索词（基于热门工具名称）
async function loadHotwords() {
  try {
    const tools = await toolsApi.getList({ mode: 'all', sort: 'hot', limit: 8 })
    hotwords.value = tools.slice(0, 8).map(t => t.name)
  } catch (e) {
    // 静默处理，使用默认热词
    hotwords.value = ['ChatGPT', 'Claude', 'Midjourney', 'Stable Diffusion', 'AI写作', '代码助手']
  }
}

function handleSearchBlur() {
  // 延迟关闭，让点击事件有时间触发
  setTimeout(() => {
    showHotwords.value = false
  }, 200)
}

function handleHotwordClick(word) {
  searchInput.value = word
  showHotwords.value = false
  doSearch(word)
}

function handleHistoryClick(keyword) {
  searchInput.value = keyword
  showHotwords.value = false
  doSearch(keyword)
}

function handleDeleteHistory(id) {
  deleteHistory(id)
}

function handleClearHistory() {
  clearHistory()
}

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
    const params = {
      mode: 'all',
      sort: sortBy.value
    }
    if (selectedTagId.value) {
      params.tag_id = selectedTagId.value
    }
    globalTools.value = await toolsApi.getList(params)
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
    // 记录搜索历史
    addHistory(keyword)
  } catch (error) {
    console.error('搜索失败:', error)
  }
}

function handleCategorySelect(index) {
  activeCategory.value = index
}

async function handleLogin() {
  if (!isInFeishu()) {
    ElMessage.warning('请在飞书客户端中打开')
    return
  }

  // 跳转到登录页
  router.push('/login')
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
  background: var(--bg-primary);
}

/* 顶部栏 - 玻璃拟态效果 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: -0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.favorites-link,
.want-tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.95);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.favorites-link:hover,
.want-tool-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px 4px 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  backdrop-filter: blur(8px);
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}

/* 主题切换按钮 */
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: rotate(15deg);
}

/* 模式切换栏 */
.mode-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.mode-tabs {
  display: flex;
  gap: 6px;
  background: var(--bg-tertiary);
  padding: 4px;
  border-radius: 12px;
}

.mode-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.mode-tab:hover {
  color: var(--accent-color);
}

.mode-tab.active {
  background: var(--bg-secondary);
  color: var(--accent-color);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.mode-tab .el-icon {
  font-size: 16px;
}

.search-box {
  flex: 1;
  max-width: 480px;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  padding: 4px 16px;
  transition: all 0.3s;
}

.search-box :deep(.el-input__wrapper:hover),
.search-box :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
}

.sort-box {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  background: var(--bg-tertiary);
  padding: 6px 12px;
  border-radius: 8px;
}

.sort-box :deep(.el-select) {
  width: 100px;
}

.sort-box :deep(.el-select .el-input__wrapper) {
  box-shadow: none;
  background: var(--bg-secondary);
}

.sort-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

/* 标签筛选栏 */
.tag-filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.tag-filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.tag-filter-label .el-icon {
  color: var(--accent-color);
}

.tag-filter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;
}

.tag-filter-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--bg-tertiary);
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.tag-filter-item:hover {
  border-color: var(--accent-color);
  background: var(--accent-light);
}

.tag-filter-item.active {
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.tag-filter-item .tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-clear-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 20px;
  background: transparent;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}

.tag-clear-btn:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

/* 搜索面板 */
.search-panel {
  padding: 8px 4px;
}

.history-section,
.hotwords-section {
  margin-bottom: 16px;
}

.history-section:last-child,
.hotwords-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.section-title .el-icon {
  color: var(--accent-color);
}

.hotwords-section .section-title .el-icon {
  color: #f56c6c;
}

.clear-btn {
  padding: 4px 10px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-btn:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

/* 搜索历史列表 */
.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  background: var(--bg-tertiary);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s;
}

.history-item:hover {
  background: var(--accent-light);
}

.history-text {
  padding: 6px 12px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-text:hover {
  color: var(--accent-color);
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #f56c6c;
}

/* 热词列表 */
.hotwords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hotword-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.hotword-tag:hover {
  background: var(--accent-light);
  color: var(--accent-color);
}

.hotword-tag.is-top {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.1), rgba(230, 162, 60, 0.1));
}

.hotword-tag.is-top .hotword-rank {
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
  color: #fff;
}

.hotword-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--text-muted);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
}

.hotword-text {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 主体区域 */
.main-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.02);
}

.sidebar-loading {
  padding: 20px;
}

.category-menu {
  border-right: none;
  padding: 8px;
}

.category-menu :deep(.el-menu-item),
.category-menu :deep(.el-sub-menu__title) {
  border-radius: 10px;
  margin: 2px 0;
  transition: all 0.2s;
}

.category-menu :deep(.el-menu-item:hover),
.category-menu :deep(.el-sub-menu__title:hover) {
  background: linear-gradient(135deg, #667eea10, #764ba210);
}

.category-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #667eea15, #764ba215);
  color: #667eea;
  font-weight: 600;
}

.cat-item-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
}

.cat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  margin-right: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.cat-name {
  flex: 1;
}

.child-item-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
}

.child-name {
  flex: 1;
}

/* 工具数量角标 */
.tool-badge {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.category-menu :deep(.el-menu-item.is-active) .tool-badge {
  background: #fff;
  color: #667eea;
}

.category-menu :deep(.child-menu-item) {
  padding-right: 40px !important;
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.content-loading {
  background: var(--bg-secondary);
  padding: 24px;
  border-radius: 16px;
  box-shadow: var(--shadow-md);
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--bg-tertiary);
}

.category-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.category-title::before {
  content: '';
  width: 4px;
  height: 24px;
  background: var(--accent-gradient);
  border-radius: 2px;
}

.tool-total {
  font-size: 14px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 6px 14px;
  border-radius: 20px;
}

.empty {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 80px 40px;
  box-shadow: var(--shadow-md);
  text-align: center;
}

.login-prompt {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 100px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .tool-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }

  .title {
    font-size: 18px;
  }

  .sidebar {
    display: none;
  }

  .mode-bar {
    flex-wrap: wrap;
    padding: 12px 16px;
    gap: 12px;
  }

  .search-box {
    width: 100%;
    max-width: none;
    order: 10;
  }

  .sort-box {
    order: 5;
    margin-left: 0;
  }

  .content {
    padding: 16px;
  }

  .tool-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .content-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .category-title {
    font-size: 18px;
  }
}

/* 平滑滚动 */
.content,
.sidebar {
  scroll-behavior: smooth;
}

/* 自定义滚动条 */
.content::-webkit-scrollbar,
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.content::-webkit-scrollbar-track,
.sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.content::-webkit-scrollbar-thumb,
.sidebar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 3px;
}

.content::-webkit-scrollbar-thumb:hover,
.sidebar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}

/* 快捷键帮助浮动按钮 */
.shortcuts-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: var(--accent-gradient);
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 50;
}

.shortcuts-fab:hover {
  transform: scale(1.1) translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5);
}

.shortcuts-fab:active {
  transform: scale(0.95);
}

/* 快捷键帮助弹窗 */
.shortcuts-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.shortcuts-content {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 0;
  min-width: 360px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.shortcuts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: var(--accent-gradient);
  color: #fff;
}

.shortcuts-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.shortcuts-list {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  transition: all 0.2s;
}

.shortcut-item:hover {
  background: var(--accent-light);
}

.shortcut-keys {
  display: flex;
  gap: 6px;
}

.shortcut-keys kbd,
.shortcuts-footer kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  box-shadow: 0 2px 0 var(--border-color);
}

.shortcut-desc {
  font-size: 14px;
  color: var(--text-secondary);
}

.shortcuts-footer {
  padding: 16px 24px;
  background: var(--bg-tertiary);
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
}

.shortcuts-footer kbd {
  margin: 0 4px;
}

/* 移动端隐藏快捷键功能 */
@media (max-width: 768px) {
  .shortcuts-fab {
    display: none;
  }
}
</style>
