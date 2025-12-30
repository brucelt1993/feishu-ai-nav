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
