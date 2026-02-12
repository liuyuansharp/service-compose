export const useAuthSession = ({
  authToken,
  authorizedFetch,
  currentUser,
  refreshStatus,
  startDashboardSSE,
  startUptimeTicker,
  buildApiUrl,
  cleanupRealtime,
  closeMetrics,
  resetServiceInfoState,
  selectedService,
  logs,
  logsMeta,
  logOffset,
  logHasMorePrev,
  logHasMoreNext,
  resetMetricsHistory,
  baseLogout,
}) => {
  const logout = (silent = false) => {
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
    baseLogout(silent)
  }

  const bootstrapSession = async () => {
    if (!authToken.value) return
    try {
      const response = await authorizedFetch('/api/me')
      const user = await response.json()
      currentUser.value = user
      await refreshStatus()
      startDashboardSSE(authToken, buildApiUrl)
      startUptimeTicker()
    } catch (error) {
      if (error.message === 'Unauthorized') return
      console.error('Bootstrap session error:', error)
    }
  }

  return {
    logout,
    bootstrapSession,
  }
}
