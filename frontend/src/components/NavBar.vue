<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { isLoggedIn, currentUsername, logout } = useAuth()

function goLogin() {
  router.push('/login')
}

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <header class="nav-bar">
    <div class="nav-bar__brand">
      <span class="nav-bar__title">脚手架安全计算</span>
      <span class="nav-bar__tag">盘扣式双排外脚手架</span>
    </div>

    <div class="nav-bar__actions">
      <nav class="nav-bar__links">
        <router-link to="/" active-class="is-active">计算</router-link>
        <router-link to="/history" active-class="is-active">历史</router-link>
        <router-link to="/specs" active-class="is-active">规范</router-link>
      </nav>
      <button v-if="!isLoggedIn" class="nav-bar__login" type="button" @click="goLogin">
        登录
      </button>
      <div v-else class="nav-bar__user">
        <span class="nav-bar__username">你好，{{ currentUsername }}</span>
        <button class="nav-bar__login" type="button" @click="handleLogout">退出</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.nav-bar {
  height: 48px;
  padding: 0 18px 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1a3a6b;
  color: #ffffff;
}

.nav-bar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-bar__title {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.nav-bar__tag {
  padding: 2px 8px;
  border-radius: 3px;
  background: #4a90d9;
  color: #ffffff;
  font-size: 10px;
  line-height: 1.4;
}

.nav-bar__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-bar__links {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
}

.nav-bar__links a {
  color: rgba(255, 255, 255, 0.6);
  transition: color 0.2s ease;
}

.nav-bar__links a.is-active,
.nav-bar__links a:hover {
  color: #ffffff;
}

.nav-bar__login {
  border: none;
  border-radius: 4px;
  padding: 5px 14px;
  background: #4a90d9;
  color: #ffffff;
  font-size: 12px;
  cursor: pointer;
}

.nav-bar__user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-bar__username {
  color: #ffffff;
  font-size: 12px;
}
</style>
