<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginUser, registerUser } from '../api/scaffold.js'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const { login } = useAuth()

const activeTab = ref('login')
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

function getErrorMessage(error, fallbackMessage) {
  const message = error?.response?.data?.message
  const detail = error?.response?.data?.detail

  if (typeof message === 'string' && message.trim()) {
    return message.trim()
  }

  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || JSON.stringify(item))
      .filter(Boolean)
      .join('；')
  }

  return fallbackMessage
}

function getLoginErrorMessage(error) {
  const message = error?.response?.data?.message
  return typeof message === 'string' && message.trim() ? message.trim() : '登录失败，请稍后重试'
}

async function handleLogin() {
  loginLoading.value = true

  try {
    const res = await loginUser({
      username: loginForm.username,
      password: loginForm.password
    })

    login(res.data.access_token, res.data.username)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(getLoginErrorMessage(error))
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }

  registerLoading.value = true

  try {
    await registerUser({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })

    activeTab.value = 'login'
    ElMessage.success('注册成功，请登录')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '注册失败，请稍后重试'))
  } finally {
    registerLoading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <div class="login-header">
        <h1>脚手架安全计算平台</h1>
      </div>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form class="auth-form" :model="loginForm" label-position="top">
            <el-form-item label="用户名或邮箱">
              <el-input v-model="loginForm.username" placeholder="用户名或邮箱" clearable />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>
            <el-button
              class="auth-submit"
              type="primary"
              :loading="loginLoading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form class="auth-form" :model="registerForm" label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" clearable />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" clearable />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
              <div class="password-hint">密码须至少8位，包含字母和数字</div>
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
              />
            </el-form-item>
            <el-button
              class="auth-submit"
              type="primary"
              :loading="registerLoading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.login-card {
  width: 400px;
  border-radius: 12px;
}

.login-header {
  text-align: center;
  margin-bottom: 18px;
}

.login-header h1 {
  margin: 0;
  color: #2f3440;
  font-size: 22px;
  font-weight: 700;
}

.auth-form {
  padding-top: 8px;
}

.password-hint {
  margin-top: 4px;
  color: var(--el-color-info);
  font-size: 12px;
  line-height: 1.4;
  text-align: left;
}

.auth-submit {
  width: 100%;
  margin-top: 8px;
}
</style>
