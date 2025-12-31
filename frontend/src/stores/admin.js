/**
 * 管理员状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminAuthApi } from '@/api'

const ADMIN_TOKEN_KEY = 'admin_token'
const ADMIN_INFO_KEY = 'admin_info'

export const useAdminStore = defineStore('admin', () => {
  // 状态
  const token = ref(localStorage.getItem(ADMIN_TOKEN_KEY) || '')
  const adminInfo = ref(JSON.parse(localStorage.getItem(ADMIN_INFO_KEY) || 'null'))

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)

  // 获取认证头
  function getAuthHeader() {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  // 登录
  async function login(username, password) {
    const res = await adminAuthApi.login(username, password)
    token.value = res.token
    adminInfo.value = res.admin
    localStorage.setItem(ADMIN_TOKEN_KEY, res.token)
    localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(res.admin))
    return res
  }

  // 登出
  function logout() {
    token.value = ''
    adminInfo.value = null
    localStorage.removeItem(ADMIN_TOKEN_KEY)
    localStorage.removeItem(ADMIN_INFO_KEY)
  }

  // 检查登录状态
  async function checkAuth() {
    if (!token.value) return false
    try {
      const res = await adminAuthApi.getMe()
      adminInfo.value = res
      localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(res))
      return true
    } catch (e) {
      logout()
      return false
    }
  }

  return {
    token,
    adminInfo,
    isLoggedIn,
    getAuthHeader,
    login,
    logout,
    checkAuth,
  }
})
