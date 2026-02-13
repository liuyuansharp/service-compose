import { ref, reactive, computed, nextTick } from 'vue'

export function useServices({ authorizedFetch, showNotification, t, currentUser, openConfirmDialog } = {}) {
  const servicesStatus = ref([])
  const isPopoutMode = ref(false)
  const serviceViewMode = ref('list')
  const serviceGraph = ref({ nodes: [], edges: [] })
  const serviceGraphLoading = ref(false)
  const controlling = ref(false)

  // ---- 服务卡片拖拽排序 ----
  const dragState = reactive({ dragging: null, over: null })
  let _orderSavePending = false
  let _saveOrderTimer = null

  function mergeServicesData(incoming) {
    if (!servicesStatus.value.length || !_orderSavePending) {
      servicesStatus.value = incoming
      return
    }
    const map = new Map(incoming.map(s => [s.name, s]))
    const merged = []
    for (const local of servicesStatus.value) {
      if (map.has(local.name)) {
        merged.push(map.get(local.name))
        map.delete(local.name)
      }
    }
    for (const s of map.values()) merged.push(s)
    servicesStatus.value = merged
  }

  function saveServiceOrder(order) {
    _orderSavePending = true
    clearTimeout(_saveOrderTimer)
    _saveOrderTimer = setTimeout(async () => {
      try {
        await authorizedFetch('/api/preferences/service-order', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order })
        })
      } catch (e) {
        console.warn('Failed to save service order:', e)
      } finally {
        _orderSavePending = false
      }
    }, 300)
  }

  const serviceCardId = (name) => `service-card-${String(name).replace(/[^a-zA-Z0-9_-]/g, '-')}`

  function onDragStart(e, serviceName) {
    dragState.dragging = serviceName
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', serviceName)
    requestAnimationFrame(() => {
      const el = document.getElementById(serviceCardId(serviceName))
      if (el) el.classList.add('drag-ghost')
    })
  }
  function onDragEnd() {
    if (dragState.dragging) {
      const el = document.getElementById(serviceCardId(dragState.dragging))
      if (el) el.classList.remove('drag-ghost')
    }
    dragState.dragging = null
    dragState.over = null
  }
  function onDragOver(e, serviceName) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (dragState.over !== serviceName) {
      dragState.over = serviceName
    }
  }
  function onDragLeave(e, serviceName) {
    const card = document.getElementById(serviceCardId(serviceName))
    if (card && !card.contains(e.relatedTarget)) {
      if (dragState.over === serviceName) dragState.over = null
    }
  }
  function onDrop(e, targetName) {
    e.preventDefault()
    const srcName = dragState.dragging
    if (!srcName || srcName === targetName) {
      onDragEnd()
      return
    }
    const list = servicesStatus.value.map(s => s.name)
    const srcIdx = list.indexOf(srcName)
    const tgtIdx = list.indexOf(targetName)
    if (srcIdx < 0 || tgtIdx < 0) { onDragEnd(); return }
    const arr = [...servicesStatus.value]
    const [removed] = arr.splice(srcIdx, 1)
    arr.splice(tgtIdx, 0, removed)
    servicesStatus.value = arr
    saveServiceOrder(arr.map(s => s.name))
    onDragEnd()
  }

  const getHealthState = (item) => {
    if (!item) return 'stopped'
    return item.health || (item.running ? 'running' : 'stopped')
  }

  const getHealthLabel = (health) => {
    if (health === 'running') return `🟢 ${t('running')}`
    if (health === 'abnormal') return `🟡 ${t('abnormal')}`
    return `🔴 ${t('stopped')}`
  }

  const getHealthTextClass = (health) => {
    if (health === 'running') return 'text-green-600'
    if (health === 'abnormal') return 'text-yellow-600'
    return 'text-red-600'
  }

  const getHealthBorderClass = (health) => {
    if (health === 'running') return 'border-l-4 border-green-500 ring-1 ring-green-300/60'
    if (health === 'abnormal') return 'border-l-4 border-yellow-500 ring-1 ring-yellow-300/60'
    return 'border-l-4 border-slate-300 ring-1 ring-slate-200/70'
  }

  const getHealthBgClass = (health) => {
    if (health === 'running') return 'bg-green-50/70 dark:bg-emerald-950/30'
    if (health === 'abnormal') return 'bg-yellow-50/70 dark:bg-yellow-900/25'
    return 'bg-slate-200/70 dark:bg-slate-800/60'
  }

  const getHealthTooltip = (item) => {
    const reason = item?.health_reason
    if (!reason && item?.health === 'abnormal') return t('heartbeat_failed')
    if (reason === 'missing') return t('heartbeat_missing')
    if (reason === 'timeout') return t('heartbeat_timeout')
    if (reason === 'connection_error') return t('heartbeat_connection_error')
    if (reason === 'invalid_url') return t('heartbeat_invalid_url')
    if (reason === 'mock_fail') return t('heartbeat_mock_failed')
    if (typeof reason === 'string' && reason.startsWith('http_status_')) {
      const code = reason.replace('http_status_', '') || 'unknown'
      return t('heartbeat_http_error', { code })
    }
    if (reason === 'heartbeat_failed') return t('heartbeat_failed')
    if (item?.health === 'abnormal') return t('abnormal')
    return ''
  }

  const overallHealth = computed(() => {
    if (!servicesStatus.value.length) return 'stopped'
    let hasAbnormal = false
    for (const service of servicesStatus.value) {
      const health = getHealthState(service)
      if (health === 'stopped') return 'stopped'
      if (health === 'abnormal') hasAbnormal = true
    }
    return hasAbnormal ? 'abnormal' : 'running'
  })
  const overallHealthLabel = computed(() => getHealthLabel(overallHealth.value))
  const overallHealthTextClass = computed(() => getHealthTextClass(overallHealth.value))
  const overallHealthTooltip = computed(() => {
    if (overallHealth.value !== 'abnormal') return ''
    const abnormalService = servicesStatus.value.find(s => getHealthState(s) === 'abnormal')
    return abnormalService ? getHealthTooltip(abnormalService) : t('abnormal')
  })

  const getServiceHealthLabel = (service) => getHealthLabel(getHealthState(service))
  const getServiceHealthTextClass = (service) => getHealthTextClass(getHealthState(service))
  const getServiceBorderClass = (service) => getHealthBorderClass(getHealthState(service))

  const statusAlerts = computed(() => {
    const items = []
    servicesStatus.value.forEach((service) => {
      const health = getHealthState(service)
      if (health !== 'running' && isCardVisible('service:' + service.name)) {
        items.push({ key: `service:${service.name}`, name: service.name, health })
      }
    })

    return items
      .map((item) => {
        const isStopped = item.health === 'stopped'
        return {
          ...item,
          level: isStopped ? 'critical' : 'warning',
          title: isStopped ? t('alert_stopped_title') : t('alert_abnormal_title'),
          message: `${item.name} (${isStopped ? t('stopped') : t('abnormal')})`
        }
      })
      .sort((a, b) => {
        if (a.level === b.level) return 0
        return a.level === 'critical' ? -1 : 1
      })
  })

  const statusAlertVisibility = ref({})
  const focusedAlertKey = ref('')
  let focusAlertTimer = null

  const focusAlertTarget = async (alert) => {
    if (!alert?.key) return
    focusedAlertKey.value = alert.key
    if (focusAlertTimer) clearTimeout(focusAlertTimer)
    focusAlertTimer = setTimeout(() => {
      focusedAlertKey.value = ''
    }, 4000)

    await nextTick()
    const targetId = serviceCardId(alert.name)
    const target = typeof document !== 'undefined' ? document.getElementById(targetId) : null
    if (target?.scrollIntoView) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  const isFocusedTarget = (key) => focusedAlertKey.value === key

  const runningCount = computed(() => {
    return visibleServices.value.filter(s => getHealthState(s) === 'running').length
  })

  const allServicesRunning = computed(() => {
    return visibleServices.value.length > 0 && runningCount.value === visibleServices.value.length
  })

  const noServicesRunning = computed(() => {
    return runningCount.value === 0
  })

  // ---- Batch Control ----
  const batchTargetServices = ref([])
  const batchSelectedServices = ref(new Set())

  const batchAllSelected = computed(() => {
    return batchTargetServices.value.length > 0 && batchSelectedServices.value.size === batchTargetServices.value.length
  })

  const batchNoneSelected = computed(() => {
    return batchSelectedServices.value.size === 0
  })

  const toggleBatchService = (name) => {
    const s = new Set(batchSelectedServices.value)
    if (s.has(name)) {
      s.delete(name)
    } else {
      s.add(name)
    }
    batchSelectedServices.value = s
  }

  const toggleBatchSelectAll = () => {
    if (batchSelectedServices.value.size === batchTargetServices.value.length) {
      batchSelectedServices.value = new Set()
    } else {
      batchSelectedServices.value = new Set(batchTargetServices.value.map(s => s.name))
    }
  }

  const executeBatchControl = async (action) => {
    controlling.value = true
    try {
      const targets = [...batchSelectedServices.value]
      const response = await authorizedFetch('/api/batch-control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, services: targets })
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `Batch ${action} failed`)
      }
      const data = await response.json()
      const { succeeded = 0, failed = 0, skipped = 0 } = data
      if (failed === 0 && skipped === 0) {
        showNotification(t('batch_action_success', { action: t(action) }), 'success')
      } else if (succeeded > 0) {
        const parts = []
        if (failed > 0) parts.push(`${failed} ${t('batch_result_failed')}`)
        if (skipped > 0) parts.push(`${skipped} ${t('batch_result_skipped')}`)
        showNotification(t('batch_action_success', { action: t(action) }) + ` (${parts.join(', ')})`, 'warning')
      } else {
        showNotification(t('batch_action_failed', { action: t(action) }), 'error')
      }
    } catch (error) {
      console.error('Batch control error:', error)
      showNotification(error.message || t('batch_action_failed', { action: t(action) }), 'error')
    } finally {
      controlling.value = false
    }
  }

  const batchControlAll = async (action) => {
    const isStart = action === 'start'
    const filtered = visibleServices.value.filter(s => {
      const state = getHealthState(s)
      return isStart ? state !== 'running' : state === 'running'
    })
    if (filtered.length === 0) {
      showNotification(t(isStart ? 'batch_no_start_targets' : 'batch_no_stop_targets'), 'info')
      return
    }
    batchTargetServices.value = filtered
    batchSelectedServices.value = new Set(filtered.map(s => s.name))
    if (openConfirmDialog) {
      openConfirmDialog({
        type: action,
        title: t(isStart ? 'batch_start_all' : 'batch_stop_all'),
        message: t(isStart ? 'batch_start_confirm' : 'batch_stop_confirm'),
        confirmText: t(isStart ? 'start' : 'stop'),
        onConfirm: () => executeBatchControl(action),
      })
    }
  }

  const isCardVisible = (cardKey) => {
    const vc = currentUser?.value?.visible_cards
    if (!vc || vc.length === 0) return true
    return vc.includes(cardKey)
  }

  const visibleServices = computed(() => {
    const vc = currentUser?.value?.visible_cards
    if (!vc || vc.length === 0) return servicesStatus.value
    return servicesStatus.value.filter(s => vc.includes('service:' + s.name))
  })

  const allCardOptions = computed(() => {
    const opts = [
      { value: 'overview', label: t('card_overview'), desc: t('card_overview_desc') },
    ]
    for (const s of servicesStatus.value) {
      opts.push({ value: 'service:' + s.name, label: s.name, desc: t('card_service_desc', { name: s.name }) })
    }
    return opts
  })

  const loadServiceGraph = async () => {
    serviceGraphLoading.value = true
    try {
      const response = await authorizedFetch('/api/services/graph')
      if (!response.ok) throw new Error('Failed to fetch graph')
      const data = await response.json()
      serviceGraph.value = {
        nodes: Array.isArray(data.nodes) ? data.nodes : [],
        edges: Array.isArray(data.edges) ? data.edges : []
      }
    } catch (error) {
      console.error('Error loading service graph:', error)
      showNotification(t('workflow_load_failed'), 'error')
    } finally {
      serviceGraphLoading.value = false
    }
  }

  const popoutWorkflow = () => {
    const url = new URL(window.location.href)
    url.searchParams.set('view', 'workflow')
    const w = 1200, h = 820
    const left = (screen.width - w) / 2, top = (screen.height - h) / 2
    window.open(url.toString(), '_blank',
      `width=${w},height=${h},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no,resizable=yes`)
  }

  const applyWorkflowViewFromUrl = () => {
    try {
      const params = new URLSearchParams(window.location.search)
      if (params.get('view') === 'workflow') {
        serviceViewMode.value = 'workflow'
        isPopoutMode.value = true
      }
    } catch (_) {}
  }

  return {
    servicesStatus,
    isPopoutMode,
    serviceViewMode,
    serviceGraph,
    serviceGraphLoading,
    controlling,
    dragState,
    mergeServicesData,
    saveServiceOrder,
    onDragStart,
    onDragEnd,
    onDragOver,
    onDragLeave,
    onDrop,
    getHealthState,
    getHealthLabel,
    getHealthTextClass,
    getHealthBorderClass,
    getHealthBgClass,
    getHealthTooltip,
    overallHealth,
    overallHealthLabel,
    overallHealthTextClass,
    overallHealthTooltip,
    getServiceHealthLabel,
    getServiceHealthTextClass,
    getServiceBorderClass,
    statusAlerts,
    statusAlertVisibility,
    focusedAlertKey,
    focusAlertTarget,
    isFocusedTarget,
    runningCount,
    allServicesRunning,
    noServicesRunning,
    batchTargetServices,
    batchSelectedServices,
    batchAllSelected,
    batchNoneSelected,
    toggleBatchService,
    toggleBatchSelectAll,
    executeBatchControl,
    batchControlAll,
    isCardVisible,
    visibleServices,
    allCardOptions,
    serviceCardId,
    loadServiceGraph,
    popoutWorkflow,
    applyWorkflowViewFromUrl,
  }
}
