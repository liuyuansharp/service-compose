import { ref, reactive, computed } from 'vue'

export function useServiceInfo({
  authorizedFetch,
  buildApiUrl,
  showNotification,
  t,
  authToken,
  servicesStatus,
  lang,
}) {
  const cpuCoresVisible = ref(false)
  const diskDetailsVisible = ref(false)
  const diskDetails = ref([])
  const diskLoading = ref(false)
  const diskError = ref('')

  const serviceInfoVisible = ref(false)
  const serviceInfoLoading = ref(false)
  const serviceInfoError = ref('')
  const serviceInfo = ref(null)

  const updateFileInput = ref(null)
  const uploadingUpdate = ref(false)
  const updatingService = ref(false)
  const uploadProgress = ref(0)
  const updateProgress = ref(0)
  const updateStatus = ref('')
  let updateTaskId = null
  let updatePoller = null

  const backupsLoading = ref(false)
  const backupsError = ref('')
  const backupOptions = ref([])
  const selectedBackup = ref('')
  const rollbackConfirmVisible = ref(false)
  const rollbackPendingBackup = ref('')

  const schedForm = reactive({ enabled: false, time: '03:00', weekdays: [] })
  const currentSchedNext = ref(null)

  const weekdayLabels = computed(() => {
    return lang.value === 'zh'
      ? ['一', '二', '三', '四', '五', '六', '日']
      : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  })

  const toggleWeekday = (idx) => {
    const i = schedForm.weekdays.indexOf(idx)
    if (i >= 0) schedForm.weekdays.splice(i, 1)
    else schedForm.weekdays.push(idx)
  }

  const saveScheduledRestart = async () => {
    if (!serviceInfo.value) return
    const serviceName = serviceInfo.value.name
    const cron = schedForm.enabled
      ? schedForm.time + (schedForm.weekdays.length ? '@' + schedForm.weekdays.sort().join(',') : '')
      : ''
    try {
      const response = await authorizedFetch('/api/scheduled-restart', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service: serviceName, enabled: schedForm.enabled, cron })
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed')
      }
      const data = await response.json()
      currentSchedNext.value = data.next_restart || null
      showNotification(t('sched_saved'), 'success')
    } catch (e) {
      showNotification(e.message, 'error')
    }
  }

  const openCpuCores = async () => {
    cpuCoresVisible.value = true
  }

  const closeCpuCores = () => {
    cpuCoresVisible.value = false
  }

  const openDiskDetails = async () => {
    diskDetailsVisible.value = true
    diskLoading.value = true
    diskError.value = ''
    try {
      const response = await authorizedFetch('/api/disks')
      if (!response.ok) throw new Error('Failed to load disk info')
      const data = await response.json()
      diskDetails.value = Array.isArray(data) ? data : []
    } catch (error) {
      diskError.value = error.message || t('disk_details_failed')
      showNotification(t('disk_details_failed'), 'error')
    } finally {
      diskLoading.value = false
    }
  }

  const closeDiskDetails = () => {
    diskDetailsVisible.value = false
  }

  const loadServiceInfo = async (serviceName) => {
    serviceInfoLoading.value = true
    serviceInfoError.value = ''
    try {
      const response = await authorizedFetch(`/api/info?service=${encodeURIComponent(serviceName)}`)
      if (!response.ok) throw new Error('Failed to load info')
      const data = await response.json()
      const statusData = servicesStatus.value.find(s => s.name === serviceName)
      if (statusData?.scheduled_restart) {
        data.scheduled_restart = statusData.scheduled_restart
      }
      serviceInfo.value = data
    } catch (error) {
      serviceInfoError.value = error.message || t('info_failed')
      showNotification(t('info_failed'), 'error')
    } finally {
      serviceInfoLoading.value = false
    }
  }

  const loadBackups = async (serviceName) => {
    backupsLoading.value = true
    backupsError.value = ''
    try {
      const response = await authorizedFetch(`/api/update/backups?service=${encodeURIComponent(serviceName)}`)
      if (!response.ok) throw new Error('Failed to load backups')
      const data = await response.json()
      backupOptions.value = Array.isArray(data) ? data : []
      selectedBackup.value = backupOptions.value[0]?.name || ''
    } catch (error) {
      backupsError.value = error.message || t('rollback_failed')
    } finally {
      backupsLoading.value = false
    }
  }

  const openServiceInfo = async (serviceName) => {
    serviceInfoVisible.value = true
    serviceInfo.value = null
    backupsError.value = ''
    backupsLoading.value = true
    backupOptions.value = []
    selectedBackup.value = ''
    currentSchedNext.value = null
    const statusData = servicesStatus.value.find(s => s.name === serviceName)
    const sr = statusData?.scheduled_restart
    if (sr && sr.enabled) {
      schedForm.enabled = true
      const cronParts = (sr.cron || '').split('@')
      schedForm.time = cronParts[0] || '03:00'
      if (cronParts.length > 1 && cronParts[1]) {
        schedForm.weekdays = cronParts[1].split(',').map(Number).filter(d => d >= 0 && d <= 6)
      } else {
        schedForm.weekdays = []
      }
      currentSchedNext.value = sr.next_restart || null
    } else {
      schedForm.enabled = false
      schedForm.time = '03:00'
      schedForm.weekdays = []
    }
    await loadServiceInfo(serviceName)
    await loadBackups(serviceName)
  }

  const closeServiceInfo = () => {
    serviceInfoVisible.value = false
    if (updatePoller) {
      clearInterval(updatePoller)
      updatePoller = null
    }
    updateTaskId = null
    uploadingUpdate.value = false
    updatingService.value = false
    uploadProgress.value = 0
    updateProgress.value = 0
    updateStatus.value = ''
    backupOptions.value = []
    selectedBackup.value = ''
    backupsError.value = ''
    backupsLoading.value = false
    rollbackConfirmVisible.value = false
    rollbackPendingBackup.value = ''
  }

  const rollbackToSelected = () => {
    if (!serviceInfo.value || !selectedBackup.value) return
    rollbackPendingBackup.value = selectedBackup.value
    rollbackConfirmVisible.value = true
  }

  const confirmRollback = async () => {
    if (!serviceInfo.value || !rollbackPendingBackup.value) return
    rollbackConfirmVisible.value = false
    try {
      const serviceName = encodeURIComponent(serviceInfo.value.name)
      const backupName = encodeURIComponent(rollbackPendingBackup.value)
      const response = await authorizedFetch(`/api/update/rollback?service=${serviceName}&backup=${backupName}`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Rollback failed')
      showNotification(t('rollback_success'), 'success')
      await loadBackups(serviceInfo.value.name)
      await loadServiceInfo(serviceInfo.value.name)
    } catch (error) {
      showNotification(t('rollback_failed'), 'error')
    } finally {
      rollbackPendingBackup.value = ''
    }
  }

  const cancelRollback = () => {
    rollbackConfirmVisible.value = false
    rollbackPendingBackup.value = ''
  }

  const triggerUpdateUpload = () => {
    if (!serviceInfo.value) return
    updateFileInput.value?.click()
  }

  const handleUpdateFileChange = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    if (!file.name.endsWith('.tar.gz')) {
      showNotification(t('update_file_invalid'), 'error')
      event.target.value = ''
      return
    }
    uploadUpdatePackage(file)
    event.target.value = ''
  }

  const uploadUpdatePackage = (file) => {
    if (!serviceInfo.value) return
    uploadingUpdate.value = true
    updatingService.value = false
    uploadProgress.value = 0
    updateProgress.value = 0
    updateStatus.value = t('uploading')
    updateTaskId = null
    if (updatePoller) {
      clearInterval(updatePoller)
      updatePoller = null
    }

    const formData = new FormData()
    formData.append('file', file)
    const xhr = new XMLHttpRequest()
    const target = encodeURIComponent(serviceInfo.value.name || 'platform')
    xhr.open('POST', buildApiUrl(`/api/update/upload?service=${target}`))
    if (authToken.value) {
      xhr.setRequestHeader('Authorization', `Bearer ${authToken.value}`)
    }
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        uploadProgress.value = Math.round((event.loaded / event.total) * 100)
      }
    }
    xhr.onload = () => {
      uploadingUpdate.value = false
      if (xhr.status >= 200 && xhr.status < 300) {
        uploadProgress.value = 100
        try {
          const data = JSON.parse(xhr.responseText)
          updateTaskId = data.task_id
        } catch (e) {
          updateTaskId = null
        }
        if (updateTaskId) {
          updateStatus.value = t('updating')
          startUpdatePolling()
        } else {
          updateStatus.value = t('update_failed')
        }
      } else {
        updateStatus.value = t('update_failed')
        showNotification(t('update_failed'), 'error')
      }
    }
    xhr.onerror = () => {
      uploadingUpdate.value = false
      updateStatus.value = t('update_failed')
      showNotification(t('update_failed'), 'error')
    }
    xhr.send(formData)
  }

  const startUpdatePolling = () => {
    if (!updateTaskId) return
    updatingService.value = true
    updatePoller = setInterval(async () => {
      try {
        const response = await authorizedFetch(`/api/update/progress?task_id=${updateTaskId}`)
        if (!response.ok) throw new Error('Failed to load progress')
        const data = await response.json()
        updateProgress.value = data.update_progress ?? 0
        if (data.status === 'completed') {
          updateStatus.value = t('update_complete')
          updatingService.value = false
          clearInterval(updatePoller)
          updatePoller = null
        } else if (data.status === 'failed') {
          updateStatus.value = t('update_failed')
          updatingService.value = false
          clearInterval(updatePoller)
          updatePoller = null
        }
      } catch (error) {
        updateStatus.value = t('update_failed')
        updatingService.value = false
        if (updatePoller) {
          clearInterval(updatePoller)
          updatePoller = null
        }
      }
    }, 1000)
  }

  const resetServiceInfoState = () => {
    serviceInfo.value = null
    serviceInfoError.value = ''
    serviceInfoLoading.value = false
    closeServiceInfo()
    diskDetails.value = []
    diskError.value = ''
    diskLoading.value = false
  }

  return {
    cpuCoresVisible,
    openCpuCores,
    closeCpuCores,
    diskDetailsVisible,
    diskDetails,
    diskLoading,
    diskError,
    openDiskDetails,
    closeDiskDetails,
    serviceInfoVisible,
    serviceInfoLoading,
    serviceInfoError,
    serviceInfo,
    updateFileInput,
    uploadingUpdate,
    updatingService,
    uploadProgress,
    updateProgress,
    updateStatus,
    triggerUpdateUpload,
    handleUpdateFileChange,
    backupsLoading,
    backupsError,
    backupOptions,
    selectedBackup,
    rollbackConfirmVisible,
    rollbackPendingBackup,
    rollbackToSelected,
    confirmRollback,
    cancelRollback,
    schedForm,
    currentSchedNext,
    weekdayLabels,
    toggleWeekday,
    saveScheduledRestart,
    openServiceInfo,
    closeServiceInfo,
    loadServiceInfo,
    loadBackups,
    resetServiceInfoState,
  }
}
