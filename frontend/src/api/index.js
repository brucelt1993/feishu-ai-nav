import axios from 'axios'
import { useUserStore } from '@/stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    const authHeader = userStore.getAuthHeader()
    if (authHeader.Authorization) {
      config.headers.Authorization = authHeader.Authorization
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
  getList: () => api.get('/tools'),
  recordClick: (toolId) => api.post(`/tools/${toolId}/click`),
}

// ============ 飞书API ============
export const feishuApi = {
  getJsapiTicket: (url) => api.get('/feishu/jsapi_ticket', { params: { url } }),
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
}

export default api
