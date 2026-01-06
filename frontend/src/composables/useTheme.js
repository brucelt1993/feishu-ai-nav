import { ref, watch, onMounted } from 'vue'

const THEME_KEY = 'ai-nav-theme'

// 全局主题状态
const isDark = ref(false)

export function useTheme() {
  // 初始化主题
  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved) {
      isDark.value = saved === 'dark'
    } else {
      // 跟随系统
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    applyTheme()
  }

  // 切换主题
  function toggleTheme() {
    isDark.value = !isDark.value
    localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light')
    applyTheme()
  }

  // 应用主题
  function applyTheme() {
    document.documentElement.classList.toggle('dark', isDark.value)
    // 更新 meta theme-color
    const metaTheme = document.querySelector('meta[name="theme-color"]')
    if (metaTheme) {
      metaTheme.content = isDark.value ? '#1e293b' : '#667eea'
    }
  }

  // 监听系统主题变化
  onMounted(() => {
    initTheme()
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem(THEME_KEY)) {
        isDark.value = e.matches
        applyTheme()
      }
    })
  })

  return {
    isDark,
    toggleTheme
  }
}
