export const useServiceControl = ({
  authorizedFetch,
  showNotification,
  t,
  refreshStatus,
  formatControlDetails,
  schedulePostControlRefresh,
  controlling,
}) => {
  const controlService = async (action, service) => {
    controlling.value = true
    try {
      const response = await authorizedFetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, service })
      })

      if (response.status === 409) {
        const err = await response.json().catch(() => ({}))
        showNotification(err.detail || t('service_busy'), 'warning')
        return
      }
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `Failed to ${action} service`)
      }

      const data = await response.json()
      const details = formatControlDetails(data)
      showNotification(t('service_action_success', { action: t(action) }), 'success', details)
      await refreshStatus()
      schedulePostControlRefresh()
    } catch (error) {
      console.error('Control error:', error)
      showNotification(error.message || t('control_failed'), 'error')
    } finally {
      controlling.value = false
    }
  }

  return {
    controlService,
  }
}
