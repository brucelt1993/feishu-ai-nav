<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { initFeishuSDK } from '@/utils/feishu'
import { useTheme } from '@/composables/useTheme'

useTheme()

onMounted(() => {
  window.__PERF__?.mark('App.vue mounted')

  // 初始化飞书JSSDK（非阻塞，不影响页面渲染）
  initFeishuSDK()
    .then(result => {
      window.__PERF__?.mark(`飞书SDK初始化完成(${result ? '成功' : '跳过'})`)
    })
    .catch(e => {
      console.warn('SDK初始化失败:', e)
      window.__PERF__?.mark('飞书SDK初始化失败')
    })
})
</script>

<style>
/* CSS 变量 - 亮色主题 */
:root {
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f1f5f9;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border-color: rgba(0, 0, 0, 0.06);
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-color: #667eea;
  --accent-light: rgba(102, 126, 234, 0.1);
}

/* CSS 变量 - 深色主题 */
:root.dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --border-color: rgba(255, 255, 255, 0.1);
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
  --accent-gradient: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
  --accent-color: #818cf8;
  --accent-light: rgba(129, 140, 248, 0.15);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  transition: background-color 0.3s, color 0.3s;
}

#app {
  min-height: 100vh;
}

/* 深色模式下 Element Plus 样式覆盖 */
:root.dark .el-menu {
  background-color: var(--bg-secondary);
  border-color: var(--border-color);
}

:root.dark .el-menu-item,
:root.dark .el-sub-menu__title {
  color: var(--text-secondary);
}

:root.dark .el-menu-item:hover,
:root.dark .el-sub-menu__title:hover {
  background-color: var(--accent-light);
}

:root.dark .el-menu-item.is-active {
  color: var(--accent-color);
}

:root.dark .el-input__wrapper {
  background-color: var(--bg-tertiary);
  box-shadow: none;
}

:root.dark .el-input__inner {
  color: var(--text-primary);
}

:root.dark .el-input__inner::placeholder {
  color: var(--text-muted);
}

:root.dark .el-select .el-input__wrapper {
  background-color: var(--bg-tertiary);
}

:root.dark .el-button {
  --el-button-bg-color: var(--bg-tertiary);
  --el-button-border-color: var(--border-color);
  --el-button-text-color: var(--text-primary);
}

:root.dark .el-button--primary {
  --el-button-bg-color: var(--accent-color);
  --el-button-border-color: var(--accent-color);
}

:root.dark .el-skeleton__item {
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 37%, var(--bg-tertiary) 63%);
}

:root.dark .el-empty__description {
  color: var(--text-muted);
}

/* 平滑过渡 */
* {
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}
</style>
