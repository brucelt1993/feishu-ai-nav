import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useAdminStore } from '@/stores/admin'

// 错误消息映射
const ERROR_MESSAGES = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '没有访问权限',
  404: '请求的资源不存在',
  500: '服务器错误，请稍后重试',
  502: '网关错误',
  503: '服务暂时不可用',
  timeout: '请求超时，请检查网络连接',
  network: '网络连接失败，请检查网络'
}

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 管理后台接口使用管理员token
    if (config.url?.startsWith('/admin')) {
      const adminStore = useAdminStore()
      const authHeader = adminStore.getAuthHeader()
      if (authHeader.Authorization) {
        config.headers.Authorization = authHeader.Authorization
      }
    } else {
      // 普通接口使用用户token
      const userStore = useUserStore()
      const authHeader = userStore.getAuthHeader()
      if (authHeader.Authorization) {
        config.headers.Authorization = authHeader.Authorization
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 构建错误消息
    let message = '请求失败'

    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      message = ERROR_MESSAGES.timeout
    } else if (!error.response) {
      message = ERROR_MESSAGES.network
    } else {
      const status = error.response.status
      const serverMessage = error.response.data?.detail || error.response.data?.message
      message = serverMessage || ERROR_MESSAGES[status] || `请求失败 (${status})`

      // 401处理：清除登录状态
      if (status === 401) {
        const isAdminApi = error.config?.url?.startsWith('/admin')
        if (isAdminApi) {
          const adminStore = useAdminStore()
          adminStore.logout()
        } else {
          const userStore = useUserStore()
          userStore.logout()
        }
      }
    }

    // 只对非静默请求显示错误提示
    if (!error.config?.silent) {
      ElMessage.error(message)
    }

    console.error('API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      message: error.response?.data || error.message
    })

    return Promise.reject(error)
  }
)

// ============ 配置API ============
export const configApi = {
  get: () => api.get('/config'),
}

// ============ 认证API ============
export const authApi = {
  login: (code) => api.post('/auth/login', { code }),
}

// ============ 分类API ============
export const categoriesApi = {
  getTree: () => api.get('/categories'),
}

// ============ 工具API ============
export const toolsApi = {
  getList: (params = {}) => api.get('/tools', { params }),
  search: (q, limit = 20) => api.get('/tools/search', { params: { q, limit } }),
  recordClick: (toolId) => api.post(`/tools/${toolId}/click`),
  getTags: () => api.get('/tools/tags'),
  // 交互
  getStats: (toolId) => api.get(`/tools/${toolId}/stats`),
  like: (toolId) => api.post(`/tools/${toolId}/like`),
  unlike: (toolId) => api.delete(`/tools/${toolId}/like`),
  favorite: (toolId) => api.post(`/tools/${toolId}/favorite`),
  unfavorite: (toolId) => api.delete(`/tools/${toolId}/favorite`),
}

// ============ 用户API ============
export const userApi = {
  getFavorites: () => api.get('/user/favorites'),
  getFeedback: () => api.get('/user/feedback'),
  // 搜索历史
  getSearchHistory: (limit = 20) => api.get('/user/search-history', { params: { limit } }),
  addSearchHistory: (keyword) => api.post('/user/search-history', null, { params: { keyword } }),
  deleteSearchHistory: (id) => api.delete(`/user/search-history/${id}`),
  clearSearchHistory: () => api.delete('/user/search-history'),
}

// ============ 反馈API ============
export const feedbackApi = {
  create: (data) => api.post('/feedback', data),
  getList: (params) => api.get('/admin/feedback', { params }),
  getStats: () => api.get('/admin/feedback/stats'),
  update: (id, data) => api.put(`/admin/feedback/${id}`, data),
}

// ============ 飞书API ============
export const feishuApi = {
  getJsapiTicket: (url) => api.get('/feishu/jsapi_ticket', { params: { url } }),
}

// ============ 管理员认证API ============
export const adminAuthApi = {
  login: (username, password) => api.post('/admin/auth/login', { username, password }),
  getMe: () => api.get('/admin/auth/me'),
  changePassword: (oldPassword, newPassword) => api.put('/admin/auth/password', {
    old_password: oldPassword,
    new_password: newPassword
  }),
}

// ============ 管理API ============
export const adminApi = {
  // 分类管理
  getCategories: () => api.get('/admin/categories'),
  createCategory: (data) => api.post('/admin/categories', data),
  updateCategory: (id, data) => api.put(`/admin/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/admin/categories/${id}`),

  // 工具管理
  getTools: (page = 1, size = 20, categoryId) => api.get('/admin/tools', {
    params: { page, size, category_id: categoryId }
  }),
  createTool: (data) => api.post('/admin/tools', data),
  updateTool: (id, data) => api.put(`/admin/tools/${id}`, data),
  previewDeleteTool: (id) => api.get(`/admin/tools/${id}/delete-preview`),
  deleteTool: (id) => api.delete(`/admin/tools/${id}`),

  // 统计
  getOverview: () => api.get('/admin/stats/overview'),
  getToolStats: (days = 7, limit = 10) => api.get('/admin/stats/tools', { params: { days, limit } }),
  getUserStats: (days = 7, limit = 20) => api.get('/admin/stats/users', { params: { days, limit } }),
  getTrend: (days = 30) => api.get('/admin/stats/trend', { params: { days } }),
  getCategoryDistribution: () => api.get('/admin/stats/category-distribution'),
  getToolDetailStats: (toolId, days = 30) => api.get(`/admin/stats/tool/${toolId}`, { params: { days } }),

  // 数据导出
  exportToolsStats: (days = 30) => api.get('/admin/export/tools', {
    params: { days },
    responseType: 'blob'
  }),
  exportUsersStats: (days = 30) => api.get('/admin/export/users', {
    params: { days },
    responseType: 'blob'
  }),
  exportTrendStats: (days = 30) => api.get('/admin/export/trend', {
    params: { days },
    responseType: 'blob'
  }),

  // 标签管理
  getTags: () => api.get('/admin/tags'),
  createTag: (data) => api.post('/admin/tags', data),
  updateTag: (id, data) => api.put(`/admin/tags/${id}`, data),
  deleteTag: (id) => api.delete(`/admin/tags/${id}`),
  getToolTags: (toolId) => api.get(`/admin/tools/${toolId}/tags`),
  setToolTags: (toolId, tagIds) => api.put(`/admin/tools/${toolId}/tags`, tagIds),

  // 导入导出
  importTools: (file, updateExisting = true) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/admin/tools/import?update_existing=${updateExisting}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  downloadTemplate: () => api.get('/admin/tools/import/template', { responseType: 'blob' }),
}

export default api
