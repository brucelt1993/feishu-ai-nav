import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(null)
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => user.value?.name || '未登录')
  const userAvatar = computed(() => user.value?.avatar_url || '')

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(userInfo) {
    user.value = userInfo
    localStorage.setItem('userInfo', JSON.stringify(userInfo))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function getAuthHeader() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  // 初始化时从 localStorage 恢复状态
  function init() {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      token.value = storedToken
      const storedUser = localStorage.getItem('userInfo')
      if (storedUser) {
        try {
          user.value = JSON.parse(storedUser)
        } catch (e) {
          console.warn('解析用户信息失败:', e)
        }
      }
    }
  }

  // 立即初始化
  init()

  return {
    token,
    user,
    isLoggedIn,
    userName,
    userAvatar,
    setToken,
    setUser,
    logout,
    getAuthHeader
  }
})
