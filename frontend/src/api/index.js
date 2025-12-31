import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { useAdminStore } from '@/stores/admin'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
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
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

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
  deleteTool: (id) => api.delete(`/admin/tools/${id}`),

  // 统计
  getOverview: () => api.get('/admin/stats/overview'),
  getToolStats: (days = 7, limit = 10) => api.get('/admin/stats/tools', { params: { days, limit } }),
  getUserStats: (days = 7, limit = 20) => api.get('/admin/stats/users', { params: { days, limit } }),
  getTrend: (days = 30) => api.get('/admin/stats/trend', { params: { days } }),

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
