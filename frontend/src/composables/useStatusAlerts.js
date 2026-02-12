import { ref, watch } from 'vue'

export function useStatusAlerts({ statusAlerts, statusAlertVisibility }) {
  const statusAlertTimers = ref({})
  let statusAlertRepeatTimer = null

  const isStatusAlertVisible = (key) => Boolean(statusAlertVisibility.value[key])

  const showStatusAlert = (key) => {
    if (!key) return
    statusAlertVisibility.value[key] = true
    if (statusAlertTimers.value[key]) clearTimeout(statusAlertTimers.value[key])
    statusAlertTimers.value[key] = setTimeout(() => {
      statusAlertVisibility.value[key] = false
    }, 5000)
  }

  const hideStatusAlert = (key) => {
    if (!key) return
    statusAlertVisibility.value[key] = false
    if (statusAlertTimers.value[key]) clearTimeout(statusAlertTimers.value[key])
    delete statusAlertTimers.value[key]
  }

  const startRepeatAlert = () => {
    if (statusAlertRepeatTimer) return
    statusAlertRepeatTimer = setInterval(() => {
      statusAlerts.value.forEach(alert => {
        showStatusAlert(alert.key)
      })
      if (!statusAlerts.value.length) {
        stopRepeatAlert()
      }
    }, 30000)
  }

  const stopRepeatAlert = () => {
    if (statusAlertRepeatTimer) clearInterval(statusAlertRepeatTimer)
    statusAlertRepeatTimer = null
  }

  watch(
    () => statusAlerts.value,
    (alerts) => {
      const activeKeys = new Set(alerts.map(alert => alert.key))
      Object.keys(statusAlertTimers.value).forEach((key) => {
        if (!activeKeys.has(key)) {
          hideStatusAlert(key)
        }
      })

      if (!alerts.length) {
        stopRepeatAlert()
        return
      }

      alerts.forEach(alert => showStatusAlert(alert.key))
      startRepeatAlert()
    },
    { deep: true, immediate: true }
  )

  const cleanupStatusAlerts = () => {
    Object.keys(statusAlertTimers.value).forEach((key) => {
      if (statusAlertTimers.value[key]) clearTimeout(statusAlertTimers.value[key])
    })
    stopRepeatAlert()
  }

  return {
    isStatusAlertVisible,
    showStatusAlert,
    hideStatusAlert,
    cleanupStatusAlerts,
  }
}
