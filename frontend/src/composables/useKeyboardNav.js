import { ref, onMounted, onUnmounted } from 'vue'

export function useKeyboardNav(options = {}) {
  const {
    onSearch = null,
    onToggleTheme = null,
    onGoHome = null,
    onGoFavorites = null,
    onEscape = null
  } = options

  const showShortcutsHint = ref(false)

  function handleKeydown(e) {
    // 如果正在输入框中，只响应 Escape
    const isInputActive = ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)

    // Escape - 关闭弹窗/清除搜索
    if (e.key === 'Escape') {
      onEscape?.()
      document.activeElement?.blur()
      return
    }

    // 输入框中不响应其他快捷键
    if (isInputActive) return

    // Ctrl/Cmd + K - 聚焦搜索框
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault()
      onSearch?.()
      return
    }

    // / - 聚焦搜索框
    if (e.key === '/') {
      e.preventDefault()
      onSearch?.()
      return
    }

    // D - 切换主题
    if (e.key === 'd' || e.key === 'D') {
      onToggleTheme?.()
      return
    }

    // H - 回首页
    if (e.key === 'h' || e.key === 'H') {
      onGoHome?.()
      return
    }

    // F - 去收藏
    if (e.key === 'f' || e.key === 'F') {
      onGoFavorites?.()
      return
    }

    // ? - 显示快捷键提示
    if (e.key === '?') {
      showShortcutsHint.value = !showShortcutsHint.value
      return
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })

  const shortcuts = [
    { keys: ['/', 'Ctrl+K'], desc: '搜索工具' },
    { keys: ['D'], desc: '切换主题' },
    { keys: ['H'], desc: '回到首页' },
    { keys: ['F'], desc: '我的收藏' },
    { keys: ['Esc'], desc: '关闭/取消' },
    { keys: ['?'], desc: '快捷键帮助' }
  ]

  return {
    showShortcutsHint,
    shortcuts
  }
}
