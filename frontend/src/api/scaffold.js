import axios from 'axios'
import { useAuth } from '../composables/useAuth.js'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

export function calculate(params) {
  return http.post('/api/v1/calculations/exterior-scaffold/check', params, {
    headers: getAuthHeaders()
  })
}

export function getReferenceLocations() {
  return http.get('/api/v1/reference/locations')
}

export function resolveWindParams(params) {
  return http.post('/api/v1/reference/wind-params/resolve', params)
}

export function loginUser(params) {
  const formData = new URLSearchParams()
  formData.append('username', params.username)
  formData.append('password', params.password)

  return http.post('/api/v1/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

export function registerUser(params) {
  return http.post('/api/v1/auth/register', params)
}

function getAuthHeaders() {
  const { getToken } = useAuth()
  const token = getToken()

  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function getHistoryList() {
  return http.get('/api/v1/history/', {
    headers: getAuthHeaders()
  })
}

export function getHistoryDetail(recordId) {
  return http.get(`/api/v1/history/${recordId}`, {
    headers: getAuthHeaders()
  })
}

export function deleteHistory(recordId) {
  return http.delete(`/api/v1/history/${recordId}`, {
    headers: getAuthHeaders()
  })
}

export function downloadReport(reportPath) {
  const reportUrl = getReportUrl(reportPath)
  if (!reportUrl) {
    return
  }

  window.open(reportUrl)
}

export function getReportUrl(downloadUrl) {
  if (!downloadUrl) {
    return ''
  }

  if (/^https?:\/\//i.test(downloadUrl)) {
    return downloadUrl
  }

  return `${BASE_URL}${downloadUrl.startsWith('/') ? downloadUrl : `/${downloadUrl}`}`
}
