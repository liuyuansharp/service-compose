// ═══ API / WebSocket URL 构建 ═══

const runtimeConfig = typeof window !== 'undefined' ? (window.APP_CONFIG || {}) : {}
const apiBaseUrl = (runtimeConfig.apiBaseUrl || '').replace(/\/+$/, '')
const wsBaseUrl = (runtimeConfig.wsBaseUrl || '').replace(/\/+$/, '')
const platformLinkUrl = (runtimeConfig.platformLinkUrl || '').trim()

const buildApiUrl = (path) => {
  if (!path) return path
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  if (!apiBaseUrl) return path
  return `${apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
}

const buildWsUrl = (path) => {
  if (!path) return path
  if (wsBaseUrl) {
    return `${wsBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
  }
  if (apiBaseUrl) {
    const wsFromApi = apiBaseUrl.replace(/^http/, 'ws')
    return `${wsFromApi}${path.startsWith('/') ? path : `/${path}`}`
  }
  const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const isDevOnVite = window.location.port === '5173'
  const wsHost = window.location.hostname
  const wsPort = isDevOnVite ? '8080' : (window.location.port || '8080')
  return `${wsProto}://${wsHost}:${wsPort}${path.startsWith('/') ? path : `/${path}`}`
}

export function useApi() {
  return {
    apiBaseUrl,
    wsBaseUrl,
    platformLinkUrl,
    buildApiUrl,
    buildWsUrl,
  }
}
