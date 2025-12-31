import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// vConsole 控制（通过环境变量）
console.log('[vConsole] VITE_VCONSOLE:', import.meta.env.VITE_VCONSOLE)
console.log('[vConsole] window.VConsole:', typeof window.VConsole)

if (import.meta.env.VITE_VCONSOLE === 'true') {
  if (window.VConsole) {
    new window.VConsole()
    console.info('[vConsole] 调试工具已启用')
  } else {
    console.warn('[vConsole] VConsole 未加载，等待加载...')
    // 等待 VConsole 加载
    const checkVConsole = setInterval(() => {
      if (window.VConsole) {
        clearInterval(checkVConsole)
        new window.VConsole()
        console.info('[vConsole] 调试工具已启用（延迟加载）')
      }
    }, 100)
    // 5秒后停止检查
    setTimeout(() => clearInterval(checkVConsole), 5000)
  }
}

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
