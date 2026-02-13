import { ref } from 'vue'

export function useDashboard({ authorizedFetch, showNotification, t, servicesStatus, mergeServicesData } = {}) {
  const systemMetrics = ref({
    cpu_percent: 0,
    cpu_count: 0,
    cpu_percents: [],
    memory_percent: 0,
    memory_used: 0,
    memory_total: 0,
    disk_percent: 0,
    disk_used: 0,
    disk_total: 0,
    disk_free: 0,
    net_upload_speed: 0,
    net_download_speed: 0,
    run_disk_read_speed: 0,
    run_disk_write_speed: 0,
    host_ip: '',
    timestamp: ''
  })
  const lastUpdated = ref('')
  const statusFetchedAt = ref(0)
  const statusTicker = ref(0)
  const isConnected = ref(false)
  let statusInterval = null
  let dashboardEventSource = null
  let statusUptimeInterval = null

  const refreshStatus = async () => {
    try {
      const response = await authorizedFetch('/api/dashboard')
      if (!response.ok) throw new Error('Failed to fetch status')
      const data = await response.json()
      mergeServicesData(Array.isArray(data.services) ? data.services : [])
      systemMetrics.value = data.metrics
      lastUpdated.value = data.timestamp
      statusFetchedAt.value = Date.now()
      statusTicker.value = Date.now()
      isConnected.value = true
    } catch (error) {
      if (error.message === 'Unauthorized') return
      console.error('Error refreshing status:', error)
      try {
        const response = await authorizedFetch('/api/status')
        if (!response.ok) throw new Error('Failed to fetch status')
        const data = await response.json()
        mergeServicesData(Array.isArray(data.services) ? data.services : [])
        lastUpdated.value = data.timestamp
        statusFetchedAt.value = Date.now()
        statusTicker.value = Date.now()
        isConnected.value = true
      } catch (fallbackError) {
        if (fallbackError.message === 'Unauthorized') return
        isConnected.value = false
        showNotification?.(t?.('refresh_failed') || 'Refresh failed', 'error')
      }
    }
  }

  const startDashboardSSE = (authToken, buildApiUrl) => {
    if (dashboardEventSource) dashboardEventSource.close()
    if (!authToken?.value) return
    dashboardEventSource = new EventSource(buildApiUrl(`/api/dashboard/sse?token=${encodeURIComponent(authToken.value)}`))
    dashboardEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        mergeServicesData(Array.isArray(data.services) ? data.services : [])
        systemMetrics.value = data.metrics
        lastUpdated.value = data.timestamp
        statusFetchedAt.value = Date.now()
        statusTicker.value = Date.now()
        isConnected.value = true
      } catch (e) {}
    }
    dashboardEventSource.onerror = () => {
      dashboardEventSource.close()
      dashboardEventSource = null
      isConnected.value = false
      if (!dashboardEventSource && !statusInterval) {
        statusInterval = setInterval(refreshStatus, 5000)
      }
    }
  }

  const startUptimeTicker = () => {
    if (statusUptimeInterval) return
    statusUptimeInterval = setInterval(() => {
      statusTicker.value = Date.now()
    }, 1000)
  }

  const cleanupDashboard = () => {
    if (dashboardEventSource) {
      dashboardEventSource.close()
      dashboardEventSource = null
    }
    if (statusInterval) {
      clearInterval(statusInterval)
      statusInterval = null
    }
    if (statusUptimeInterval) {
      clearInterval(statusUptimeInterval)
      statusUptimeInterval = null
    }
  }

  return {
    systemMetrics,
    lastUpdated,
    statusFetchedAt,
    statusTicker,
    isConnected,
    refreshStatus,
    startDashboardSSE,
    startUptimeTicker,
    cleanupDashboard,
  }
}
