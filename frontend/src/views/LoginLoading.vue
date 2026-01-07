<template>
  <div class="login-loading">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <!-- 主体内容 -->
    <div class="content">
      <!-- Logo -->
      <div class="logo">
        <span class="logo-icon">🤖</span>
        <span class="logo-text">AI工具导航</span>
      </div>

      <!-- 加载动画 -->
      <div class="loader" v-if="!error">
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
      </div>

      <!-- 状态文字 -->
      <div class="status">
        <template v-if="error">
          <p class="status-text error">{{ error }}</p>
          <button class="retry-btn" @click="handleRetry">
            <span>重新登录</span>
          </button>
          <button class="skip-btn" @click="handleSkip" v-if="allowAnonymous">
            <span>跳过登录</span>
          </button>
        </template>
        <template v-else>
          <p class="status-text">{{ statusText }}</p>
          <p class="status-hint">正在连接飞书...</p>
        </template>
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="footer">
      <p>请确保在飞书客户端中打开</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { initFeishuSDK, feishuLogin, isInFeishu } from '@/utils/feishu'

const router = useRouter()
const userStore = useUserStore()

const statusText = ref('正在初始化...')
const error = ref('')
const allowAnonymous = import.meta.env.VITE_ALLOW_ANONYMOUS === 'true'

onMounted(async () => {
  // 如果已登录，直接跳转首页
  if (userStore.isLoggedIn) {
    router.replace('/')
    return
  }

  // 非飞书环境
  if (!isInFeishu()) {
    if (allowAnonymous) {
      // 允许匿名访问，直接跳转
      router.replace('/')
    } else {
      error.value = '请在飞书客户端中打开'
    }
    return
  }

  // 开始登录流程
  await doLogin()
})

async function doLogin() {
  error.value = ''

  try {
    // 1. 初始化 SDK
    statusText.value = '正在初始化飞书SDK...'
    const sdkReady = await initFeishuSDK()

    if (!sdkReady) {
      throw new Error('飞书SDK初始化失败')
    }

    // 2. 获取免登 code 并登录
    statusText.value = '正在获取登录凭证...'
    await feishuLogin()

    // 3. 登录成功，跳转首页
    statusText.value = '登录成功，正在跳转...'
    setTimeout(() => {
      router.replace('/')
    }, 300)

  } catch (e) {
    console.error('登录失败:', e)
    // 根据错误码显示友好提示
    if (e.errno === 2602002 || e.errString?.includes('invalid url')) {
      error.value = '应用配置错误，请联系管理员检查飞书应用URL配置'
    } else if (e.errString?.includes('cancel')) {
      error.value = '登录已取消'
    } else {
      error.value = e.message || e.errString || '登录失败，请重试'
    }
  }
}

function handleRetry() {
  doLogin()
}

function handleSkip() {
  router.replace('/')
}
</script>

<style scoped>
.login-loading {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -100px;
  animation: float 6s ease-in-out infinite;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
  animation: float 8s ease-in-out infinite reverse;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: 10%;
  animation: float 7s ease-in-out infinite 1s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}

/* 主体内容 */
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 48px;
}

.logo-icon {
  font-size: 48px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 加载动画 - 三环 */
.loader {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 32px;
}

.loader-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: rgba(255, 255, 255, 0.9);
  animation: spin 1.2s linear infinite;
}

.loader-ring:nth-child(1) {
  animation-delay: 0s;
}

.loader-ring:nth-child(2) {
  inset: 8px;
  border-top-color: rgba(255, 255, 255, 0.7);
  animation-delay: 0.15s;
  animation-duration: 1s;
}

.loader-ring:nth-child(3) {
  inset: 16px;
  border-top-color: rgba(255, 255, 255, 0.5);
  animation-delay: 0.3s;
  animation-duration: 0.8s;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 状态文字 */
.status {
  text-align: center;
}

.status-text {
  font-size: 18px;
  font-weight: 500;
  color: #fff;
  margin: 0 0 8px 0;
}

.status-text.error {
  color: #ffd666;
}

.status-hint {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

/* 按钮 */
.retry-btn, .skip-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 32px;
  margin: 16px 8px 0;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.retry-btn {
  background: #fff;
  color: #667eea;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.retry-btn:active {
  transform: translateY(0);
}

.skip-btn {
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.skip-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.6);
}

/* 底部提示 */
.footer {
  position: absolute;
  bottom: 32px;
  left: 0;
  right: 0;
  text-align: center;
}

.footer p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

/* 响应式 */
@media (max-width: 480px) {
  .logo-icon {
    font-size: 40px;
  }

  .logo-text {
    font-size: 24px;
  }

  .loader {
    width: 64px;
    height: 64px;
  }

  .status-text {
    font-size: 16px;
  }
}
</style>
