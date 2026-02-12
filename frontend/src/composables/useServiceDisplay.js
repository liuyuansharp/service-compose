export const useServiceDisplay = ({ lang, statusFetchedAt }) => {
  const formatDuration = (totalSeconds) => {
    if (totalSeconds == null || Number.isNaN(totalSeconds)) return '—'
    const seconds = Math.max(0, Math.floor(totalSeconds))
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (lang.value === 'zh') {
      return `${days}天${hours}小时${minutes}分钟${secs}秒`
    }
    return `${days}d ${hours}h ${minutes}m ${secs}s`
  }

  const getServiceUptimeDisplay = (service) => {
    const base = service?.uptime_seconds
    if (base == null) return service?.uptime || '—'
    const elapsed = Math.floor((Date.now() - statusFetchedAt.value) / 1000)
    return formatDuration(base + Math.max(elapsed, 0))
  }

  return {
    formatDuration,
    getServiceUptimeDisplay,
  }
}
