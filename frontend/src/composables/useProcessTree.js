import { ref } from 'vue'

export function useProcessTree({ authorizedFetch, showNotification, t }) {
  const showPidTree = ref(false)
  const pidTreeService = ref('')
  const pidTreeData = ref(null)
  const pidTreeLoading = ref(false)

  const openPidTree = async (serviceName) => {
    pidTreeService.value = serviceName
    showPidTree.value = true
    pidTreeData.value = null
    await loadPidTree()
  }

  const loadPidTree = async () => {
    pidTreeLoading.value = true
    try {
      const resp = await authorizedFetch(`/api/process-tree?service=${encodeURIComponent(pidTreeService.value)}`)
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      pidTreeData.value = await resp.json()
    } catch (e) {
      console.error('Failed to load process tree:', e)
      pidTreeData.value = { service: pidTreeService.value, pid: null, tree: null, flat: [] }
    } finally {
      pidTreeLoading.value = false
    }
  }

  const killPid = async (pid, killChildren = false) => {
    const msg = killChildren
      ? t('pid_tree_kill_all_confirm', { count: pidTreeData.value?.flat?.length || 0 })
      : t('pid_tree_kill_confirm', { pid })
    if (!confirm(msg)) return

    try {
      const resp = await authorizedFetch(
        `/api/process-tree/kill?pid=${pid}&service=${encodeURIComponent(pidTreeService.value)}&kill_children=${killChildren}`,
        { method: 'POST' }
      )
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${resp.status}`)
      }
      const result = await resp.json()
      showNotification(`${t('pid_tree_killed')}: PID ${result.killed.join(', ')}`, 'success')
      setTimeout(() => loadPidTree(), 800)
    } catch (e) {
      showNotification(e.message, 'error')
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  return {
    showPidTree,
    pidTreeService,
    pidTreeData,
    pidTreeLoading,
    openPidTree,
    loadPidTree,
    killPid,
    formatBytes,
  }
}
