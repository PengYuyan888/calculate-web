import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import CalculatorView from '../views/CalculatorView.vue'
import HistoryView from '../views/HistoryView.vue'
import LoginView from '../views/LoginView.vue'
import SpecsView from '../views/SpecsView.vue'

const routes = [
  { path: '/', component: CalculatorView },
  { path: '/history', component: HistoryView },
  { path: '/login', component: LoginView },
  { path: '/specs', component: SpecsView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const { isLoggedIn } = useAuth()

  if (to.path === '/history' && !isLoggedIn.value) {
    return '/login'
  }

  if (to.path === '/login' && isLoggedIn.value) {
    return '/'
  }

  return true
})

export default router
