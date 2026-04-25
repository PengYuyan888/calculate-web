// 用途：统一管理前端 JWT token 存取、登录态恢复与退出状态。
// 对外暴露：isLoggedIn、currentUsername、login、logout、getToken、initAuth。
import { ref } from 'vue'

const TOKEN_KEY = 'auth_token'

const isLoggedIn = ref(false)
const currentUsername = ref(null)

function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function parseJwtPayload(token) {
  try {
    const payload = token?.split('.')?.[1]
    if (!payload) {
      return null
    }

    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

function isTokenExpired(payload) {
  if (!payload?.exp) {
    return false
  }

  return payload.exp * 1000 <= Date.now()
}

function login(token, username) {
  saveToken(token)
  isLoggedIn.value = true
  currentUsername.value = username
}

function logout() {
  removeToken()
  isLoggedIn.value = false
  currentUsername.value = null
}

function initAuth() {
  const token = getToken()
  if (!token) {
    logout()
    return
  }

  const payload = parseJwtPayload(token)
  if (!payload || isTokenExpired(payload)) {
    logout()
    return
  }

  isLoggedIn.value = true
  currentUsername.value = payload.sub || null
}

export const useAuth = () => ({
  isLoggedIn,
  currentUsername,
  login,
  logout,
  getToken,
  initAuth
})
