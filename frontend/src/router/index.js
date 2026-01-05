import { createRouter, createWebHistory } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: 'AI工具导航' }
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: () => import('@/views/Favorites.vue'),
    meta: { title: '我的收藏' }
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/admin/Login.vue'),
    meta: { title: '管理员登录' }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Layout.vue'),
    meta: { title: '管理后台', requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '概览' }
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/Categories.vue'),
        meta: { title: '分类管理' }
      },
      {
        path: 'tools',
        name: 'AdminTools',
        component: () => import('@/views/admin/Tools.vue'),
        meta: { title: '工具管理' }
      },
      {
        path: 'stats',
        name: 'Stats',
        component: () => import('@/views/admin/Stats.vue'),
        meta: { title: '数据报表' }
      },
      {
        path: 'feedback',
        name: 'AdminFeedback',
        component: () => import('@/views/admin/Feedback.vue'),
        meta: { title: '反馈管理' }
      },
      {
        path: 'tags',
        name: 'AdminTags',
        component: () => import('@/views/admin/Tags.vue'),
        meta: { title: '标签管理' }
      },
      {
        path: 'report-push',
        name: 'ReportPush',
        component: () => import('@/views/admin/ReportPush.vue'),
        meta: { title: '报表推送' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'AI工具导航'

  // 管理后台需要登录
  if (to.meta.requiresAdmin) {
    const adminStore = useAdminStore()
    if (!adminStore.isLoggedIn) {
      next({ name: 'AdminLogin', query: { redirect: to.fullPath } })
      return
    }
  }

  next()
})

export default router
