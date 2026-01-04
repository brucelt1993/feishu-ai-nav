import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { configApi } from '@/api'

export const useConfigStore = defineStore('config', () => {
  const allowAnonymous = ref(false)
  const allowAnonymousInteraction = ref(false)
  const loaded = ref(false)

  // 是否允许交互（已登录 或 允许匿名交互）
  const canInteract = computed(() => {
    return allowAnonymousInteraction.value
  })

  async function loadConfig() {
    if (loaded.value) return

    try {
      const config = await configApi.get()
      allowAnonymous.value = config.allow_anonymous || false
      allowAnonymousInteraction.value = config.allow_anonymous_interaction || false
      loaded.value = true
    } catch (error) {
      console.error('加载配置失败:', error)
      // 使用默认值
      loaded.value = true
    }
  }

  return {
    allowAnonymous,
    allowAnonymousInteraction,
    canInteract,
    loaded,
    loadConfig,
  }
})
