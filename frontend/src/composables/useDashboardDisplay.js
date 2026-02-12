import { computed } from 'vue'

export const useDashboardDisplay = ({
  lastUpdated,
  overallHealth,
  overallHealthTextClass,
  systemMetrics,
  isCardVisible,
  t,
}) => {
  const formattedTimestamp = computed(() => {
    if (!lastUpdated.value) return '—'
    const d = new Date(lastUpdated.value)
    const pad = (n) => String(n).padStart(2, '0')
    const yyyy = d.getFullYear()
    const mm = pad(d.getMonth() + 1)
    const dd = pad(d.getDate())
    const hh = pad(d.getHours())
    const mi = pad(d.getMinutes())
    const ss = pad(d.getSeconds())
    return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
  })

  const overallStatusBorder = computed(() => {
    const health = overallHealth.value
    if (health === 'running') return 'border-green-500'
    if (health === 'abnormal') return 'border-yellow-500'
    return 'border-red-500'
  })

  const statusColor = computed(() => {
    return overallHealthTextClass.value
  })

  const getCpuColor = computed(() => {
    const cpu = systemMetrics.value.cpu_percent
    if (cpu < 50) return 'text-green-600'
    if (cpu < 80) return 'text-yellow-600'
    return 'text-red-600'
  })

  const getMemoryColor = computed(() => {
    const mem = systemMetrics.value.memory_percent
    if (mem < 50) return 'text-green-600'
    if (mem < 80) return 'text-yellow-600'
    return 'text-red-600'
  })

  const getDiskColor = computed(() => {
    const disk = systemMetrics.value.disk_percent
    if (disk < 50) return 'text-green-600'
    if (disk < 80) return 'text-yellow-600'
    return 'text-red-600'
  })

  const isCpuCritical = computed(() => systemMetrics.value.cpu_percent >= 90)
  const isMemoryCritical = computed(() => systemMetrics.value.memory_percent >= 90)
  const isDiskCritical = computed(() => systemMetrics.value.disk_percent >= 90)
  const cpuCorePercents = computed(() => systemMetrics.value.cpu_percents || [])

  const criticalItems = computed(() => {
    if (!isCardVisible('overview')) return []
    const items = []
    if (isCpuCritical.value) items.push(t('cpu_usage'))
    if (isMemoryCritical.value) items.push(t('memory_usage'))
    if (isDiskCritical.value) items.push(t('disk_usage'))
    return items
  })

  const hasCriticalAlert = computed(() => criticalItems.value.length > 0)

  return {
    formattedTimestamp,
    overallStatusBorder,
    statusColor,
    getCpuColor,
    getMemoryColor,
    getDiskColor,
    isCpuCritical,
    isMemoryCritical,
    isDiskCritical,
    cpuCorePercents,
    criticalItems,
    hasCriticalAlert,
  }
}
