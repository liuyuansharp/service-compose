import { ref, reactive, computed } from 'vue'

export function useAudit({ authorizedFetch } = {}) {
  const showAuditLog = ref(false)
  const auditLogs = ref([])
  const auditTotal = ref(0)
  const auditLoading = ref(false)
  const auditOffset = ref(0)
  const auditLimit = ref(50)
  const auditFilter = reactive({ action: '' })

  const loadAuditLogs = async () => {
    auditLoading.value = true
    try {
      const params = new URLSearchParams({ limit: auditLimit.value, offset: auditOffset.value })
      const response = await authorizedFetch(`/api/audit-logs?${params}`)
      if (response.ok) {
        const data = await response.json()
        auditLogs.value = data.logs || []
        auditTotal.value = data.total || 0
      }
    } catch (e) {
      console.error('Load audit logs error:', e)
    } finally {
      auditLoading.value = false
    }
  }

  const filteredAuditLogs = computed(() => {
    if (!auditFilter.action) return auditLogs.value
    return auditLogs.value.filter(e => e.action === auditFilter.action)
  })

  const formatAuditTime = (ts) => {
    if (!ts) return '—'
    const d = new Date(ts)
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

  const auditActionClass = (action) => {
    const map = {
      login: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
      start: 'bg-green-500/15 text-green-600 dark:text-green-400',
      stop: 'bg-red-500/15 text-red-600 dark:text-red-400',
      restart: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
      upload: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
      rollback: 'bg-orange-500/15 text-orange-600 dark:text-orange-400',
      create_user: 'bg-teal-500/15 text-teal-600 dark:text-teal-400',
      update_user: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400',
      delete_user: 'bg-rose-500/15 text-rose-600 dark:text-rose-400',
      update_schedule: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400',
    }
    return map[action] || 'bg-gray-500/15 text-gray-600 dark:text-gray-400'
  }

  return {
    showAuditLog,
    auditLogs,
    auditTotal,
    auditLoading,
    auditOffset,
    auditLimit,
    auditFilter,
    loadAuditLogs,
    filteredAuditLogs,
    formatAuditTime,
    auditActionClass,
  }
}
