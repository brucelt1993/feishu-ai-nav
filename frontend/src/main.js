import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// ========== 性能计时 ==========
const perfStart = performance.now()
console.log('[Perf] 🚀 main.js 开始执行', new Date().toISOString())

// 全局性能计时器
window.__PERF__ = {
  start: perfStart,
  marks: {},
  mark(name) {
    const now = performance.now()
    this.marks[name] = now
    const elapsed = (now - this.start).toFixed(1)
    console.log(`[Perf] ⏱️ ${name}: ${elapsed}ms`)
  },
  summary() {
    const total = (performance.now() - this.start).toFixed(1)
    console.log(`[Perf] ✅ 页面总耗时: ${total}ms`)
    console.table(
      Object.entries(this.marks).map(([name, time]) => ({
        阶段: name,
        耗时: `${(time - this.start).toFixed(1)}ms`
      }))
    )
  }
}

window.__PERF__.mark('imports完成')

// 全局错误处理 - 防止未捕获异常导致飞书检测页面异常
window.addEventListener('error', (event) => {
  console.error('[GlobalError]', event.message, event.filename, event.lineno)
  // 阻止错误冒泡，防止飞书检测到异常
  event.preventDefault()
  return true
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('[UnhandledRejection]', event.reason)
  // 阻止错误冒泡
  event.preventDefault()
})

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
window.__PERF__?.mark('createApp完成')

// Vue 应用错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('[VueError]', err, info)
  // 不向上抛出，防止页面崩溃
}

app.config.warnHandler = (msg, instance, trace) => {
  console.warn('[VueWarn]', msg)
}

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
window.__PERF__?.mark('插件注册完成')

app.mount('#app')
window.__PERF__?.mark('app.mount完成')
