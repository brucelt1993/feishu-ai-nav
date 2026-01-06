/**
 * 搜索历史 Composable
 */
import { ref, computed } from 'vue'
import { userApi } from '@/api'
import { useUserStore } from '@/stores/user'

const searchHistory = ref([])
const loading = ref(false)

export function useSearchHistory() {
  const userStore = useUserStore()

  // 是否已登录
  const isLoggedIn = computed(() => userStore.isLoggedIn)

  // 获取搜索历史
  async function fetchHistory(limit = 20) {
    if (!isLoggedIn.value) {
      searchHistory.value = []
      return
    }

    loading.value = true
    try {
      const res = await userApi.getSearchHistory(limit)
      searchHistory.value = res.items || []
    } catch (error) {
      console.error('获取搜索历史失败:', error)
      searchHistory.value = []
    } finally {
      loading.value = false
    }
  }

  // 添加搜索历史
  async function addHistory(keyword) {
    if (!isLoggedIn.value || !keyword?.trim()) return

    try {
      await userApi.addSearchHistory(keyword.trim())
      // 添加到本地列表开头
      const existing = searchHistory.value.findIndex(h => h.keyword === keyword.trim())
      if (existing >= 0) {
        searchHistory.value.splice(existing, 1)
      }
      searchHistory.value.unshift({
        id: Date.now(), // 临时ID
        keyword: keyword.trim(),
        searched_at: new Date().toISOString()
      })
      // 保持最多20条
      if (searchHistory.value.length > 20) {
        searchHistory.value.pop()
      }
    } catch (error) {
      console.error('添加搜索历史失败:', error)
    }
  }

  // 删除单条历史
  async function deleteHistory(id) {
    try {
      await userApi.deleteSearchHistory(id)
      const index = searchHistory.value.findIndex(h => h.id === id)
      if (index >= 0) {
        searchHistory.value.splice(index, 1)
      }
    } catch (error) {
      console.error('删除搜索历史失败:', error)
    }
  }

  // 清空历史
  async function clearHistory() {
    try {
      await userApi.clearSearchHistory()
      searchHistory.value = []
    } catch (error) {
      console.error('清空搜索历史失败:', error)
    }
  }

  return {
    searchHistory,
    loading,
    isLoggedIn,
    fetchHistory,
    addHistory,
    deleteHistory,
    clearHistory
  }
}
