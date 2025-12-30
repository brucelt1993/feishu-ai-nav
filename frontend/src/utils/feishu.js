import { feishuApi, authApi } from '@/api'
import { useUserStore } from '@/stores/user'

/**
 * 初始化飞书JSSDK
 */
export async function initFeishuSDK() {
  try {
    // 检查SDK是否加载
    if (!window.h5sdk) {
      console.error('飞书SDK未加载，请确保在飞书环境中打开')
      return false
    }

    // 获取jsapi_ticket配置
    const url = window.location.href.split('#')[0]
    const config = await feishuApi.getJsapiTicket(url)

    if (config.error) {
      console.error('获取JSSDK配置失败:', config.error)
      return false
    }

    // 保存appId供后续使用
    window.__FEISHU_APP_ID__ = config.appId

    // 配置JSSDK
    window.h5sdk.config({
      appId: config.appId,
      timestamp: config.timestamp,
      nonceStr: config.nonceStr,
      signature: config.signature,
      jsApiList: ['biz.user.getUserInfo'],
      onSuccess: () => {
        console.info('飞书JSSDK配置成功')
      },
      onFail: (err) => {
        console.error('飞书JSSDK配置失败:', err)
      }
    })

    // 等待ready
    await new Promise((resolve) => {
      window.h5sdk.ready(() => {
        console.info('飞书JSSDK ready')
        resolve()
      })
    })

    return true
  } catch (error) {
    console.error('初始化飞书SDK失败:', error)
    return false
  }
}

/**
 * 飞书免登获取用户信息
 */
export async function feishuLogin() {
  const userStore = useUserStore()

  return new Promise((resolve, reject) => {
    // 调用飞书JSSDK获取免登code
    window.tt.requestAuthCode({
      appId: window.__FEISHU_APP_ID__ || '',
      success: async (res) => {
        try {
          console.info('获取免登code成功:', res.code)

          // 用code换取用户信息
          const loginResult = await authApi.login(res.code)

          userStore.setToken(loginResult.token)
          userStore.setUser(loginResult.user)

          console.info('登录成功:', loginResult.user.name)
          resolve(loginResult.user)
        } catch (error) {
          console.error('登录失败:', error)
          reject(error)
        }
      },
      fail: (err) => {
        console.error('获取免登code失败:', err)
        reject(err)
      }
    })
  })
}

/**
 * 检测是否在飞书环境
 */
export function isInFeishu() {
  const ua = navigator.userAgent.toLowerCase()
  return ua.includes('lark') || ua.includes('feishu')
}

/**
 * 在飞书中打开URL
 */
export function openInFeishu(url) {
  if (isInFeishu() && window.tt) {
    window.tt.openLink({
      url: url
    })
  } else {
    window.open(url, '_blank')
  }
}
