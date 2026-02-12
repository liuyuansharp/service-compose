export const useSessionLifecycle = ({
  platformLinkUrl,
  cleanupDashboard,
  cleanupLogsSocket,
  cleanupMetricsStream,
  closeMetrics,
  resetServiceInfoState,
  selectedService,
  logs,
  logsMeta,
  logOffset,
  logHasMorePrev,
  logHasMoreNext,
  resetMetricsHistory,
}) => {
  const openPlatformLink = () => {
    if (!platformLinkUrl) return
    window.open(platformLinkUrl, '_blank', 'noopener,noreferrer')
  }

  const cleanupRealtime = () => {
    cleanupDashboard()
    cleanupLogsSocket()
    cleanupMetricsStream()
  }

  const handleUnauthorized = () => {
    cleanupRealtime()
    closeMetrics()
    resetServiceInfoState()
    selectedService.value = null
    logs.value = {}
    logsMeta.value = {}
    logOffset.value = {}
    logHasMorePrev.value = {}
    logHasMoreNext.value = {}
    resetMetricsHistory()
  }

  return {
    openPlatformLink,
    cleanupRealtime,
    handleUnauthorized,
  }
}
