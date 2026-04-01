import axios from 'axios'

const REPORT_BASE_URL = 'http://localhost:8000'

const http = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

export function calculate(params) {
  return http.post('/api/v1/calculations/exterior-scaffold/check', params)
}

export function getReportUrl(downloadUrl) {
  if (!downloadUrl) {
    return ''
  }

  if (/^https?:\/\//i.test(downloadUrl)) {
    return downloadUrl
  }

  return `${REPORT_BASE_URL}${downloadUrl.startsWith('/') ? downloadUrl : `/${downloadUrl}`}`
}
