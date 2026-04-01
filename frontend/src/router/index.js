import { createRouter, createWebHistory } from 'vue-router'
import CalculatorView from '../views/CalculatorView.vue'

const routes = [
  { path: '/', component: CalculatorView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
