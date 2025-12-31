/**
 * 导航模式状态管理
 * - category: 目录模式（左侧分类树）
 * - global: 全局模式（所有工具平铺）
 * - search: 搜索模式
 */
import { ref, computed } from 'vue'

// 全局状态
const currentMode = ref('category')
const searchKeyword = ref('')
const sortBy = ref('default') // default | hot | recent | name

export function useNavMode() {
  const isCategory = computed(() => currentMode.value === 'category')
  const isGlobal = computed(() => currentMode.value === 'global')
  const isSearch = computed(() => currentMode.value === 'search')

  function setMode(mode) {
    if (['category', 'global', 'search'].includes(mode)) {
      currentMode.value = mode
      // 切换模式时清空搜索词（除非切换到搜索模式）
      if (mode !== 'search') {
        searchKeyword.value = ''
      }
    }
  }

  function setSearchKeyword(keyword) {
    searchKeyword.value = keyword
    if (keyword) {
      currentMode.value = 'search'
    }
  }

  function setSortBy(sort) {
    if (['default', 'hot', 'recent', 'name'].includes(sort)) {
      sortBy.value = sort
    }
  }

  function clearSearch() {
    searchKeyword.value = ''
    currentMode.value = 'category'
  }

  return {
    currentMode,
    searchKeyword,
    sortBy,
    isCategory,
    isGlobal,
    isSearch,
    setMode,
    setSearchKeyword,
    setSortBy,
    clearSearch,
  }
}
