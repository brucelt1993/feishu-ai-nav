<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <span>🔧</span>
        <span class="logo-text">管理后台</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/admin">
          <el-icon><DataBoard /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/admin/categories">
          <el-icon><Grid /></el-icon>
          <span>分类管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/tools">
          <el-icon><Tools /></el-icon>
          <span>工具管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/stats">
          <el-icon><TrendCharts /></el-icon>
          <span>统计分析</span>
        </el-menu-item>
        <el-menu-item index="/admin/feedback">
          <el-icon><ChatLineSquare /></el-icon>
          <span>反馈管理</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button text @click="goHome">
          <el-icon><Back /></el-icon>
          返回首页
        </el-button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="content-header">
        <h2 class="page-title">{{ pageTitle }}</h2>
        <div class="admin-info" v-if="adminStore.isLoggedIn">
          <span class="admin-name">{{ adminStore.adminInfo?.nickname || adminStore.adminInfo?.username }}</span>
          <el-dropdown @command="handleCommand">
            <el-button text>
              <el-icon><Setting /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <div class="content-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAdminStore } from '@/stores/admin'
import { adminAuthApi } from '@/api'
import { DataBoard, Grid, Tools, TrendCharts, Back, ChatLineSquare, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  return route.meta.title || '管理后台'
})

function goHome() {
  router.push('/')
}

function handleCommand(command) {
  if (command === 'logout') {
    handleLogout()
  } else if (command === 'password') {
    handleChangePassword()
  }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    adminStore.logout()
    router.push('/admin/login')
    ElMessage.success('已退出登录')
  }).catch(() => {})
}

async function handleChangePassword() {
  try {
    const { value } = await ElMessageBox.prompt('请输入新密码', '修改密码', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^.{6,}$/,
      inputErrorMessage: '密码至少6位',
      inputType: 'password',
    })

    const { value: oldPassword } = await ElMessageBox.prompt('请输入原密码验证', '验证身份', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'password',
    })

    await adminAuthApi.changePassword(oldPassword, value)
    ElMessage.success('密码修改成功')
  } catch (e) {
    if (e !== 'cancel' && e.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    }
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f6f7;
}

.sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #ebeef5;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.admin-name {
  font-weight: 500;
}

.content-body {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
</style>
