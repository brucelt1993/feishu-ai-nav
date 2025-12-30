<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { initFeishuSDK } from '@/utils/feishu'

const userStore = useUserStore()

onMounted(async () => {
  // 初始化飞书JSSDK
  await initFeishuSDK()

  // 尝试自动登录
  const token = localStorage.getItem('token')
  if (token) {
    userStore.setToken(token)
    const userInfo = localStorage.getItem('userInfo')
    if (userInfo) {
      userStore.setUser(JSON.parse(userInfo))
    }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f6f7;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}
</style>
