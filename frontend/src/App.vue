<template>
  <div :class="['min-h-screen', isDark ? 'dark bg-slate-950 text-slate-100' : 'bg-gray-50 text-gray-900']">
    <LoginScreen
      v-if="!isAuthenticated"
      :is-dark="isDark"
      :theme-label="themeLabel"
      :lang-label="langLabel"
      :toggle-theme="toggleTheme"
      :toggle-language="toggleLanguage"
      :login-form="loginForm"
      :login-error="loginError"
      :login-loading="loginLoading"
      :handle-login="handleLogin"
      :t="t"
    />
    <AuthShell
      v-else
      :is-dark="isDark"
      :status-alerts="statusAlerts"
      :is-status-alert-visible="isStatusAlertVisible"
      :focus-alert-target="focusAlertTarget"
      :hide-status-alert="hideStatusAlert"
      :t="t"
    >
        <!-- Header -->
        <DashboardHeader
          v-if="!isPopoutMode"
          :is-admin="isAdmin"
          :is-connected="isConnected"
          :is-dark="isDark"
          :current-user="currentUser"
          :user-role="userRole"
          :lang-label="langLabel"
          :theme-label="themeLabel"
          :on-open-user-management="() => { showUserManagement = true; loadUsers() }"
          :on-open-audit-log="() => { showAuditLog = true; loadAuditLogs() }"
          :on-logout="() => logout()"
          :toggle-language="toggleLanguage"
          :toggle-theme="toggleTheme"
          :t="t"
        />

        <!-- Main Content -->
        <main :class="isPopoutMode ? 'px-2 py-2' : 'max-w-screen-2xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6 pb-12'">
          <div class="tech-shell">
            <div v-if="!isPopoutMode" class="tech-ornament"></div>
            <OverviewPanel
              :is-popout-mode="isPopoutMode"
              :has-critical-alert="hasCriticalAlert"
              :critical-items="criticalItems"
              :is-card-visible="isCardVisible"
              :overall-status-border="overallStatusBorder"
              :status-color="statusColor"
              :overall-health-label="overallHealthLabel"
              :overall-health="overallHealth"
              :overall-health-tooltip="overallHealthTooltip"
              :running-count="runningCount"
              :services-status="servicesStatus"
              :formatted-timestamp="formattedTimestamp"
              :system-metrics="systemMetrics"
              :get-cpu-color="getCpuColor"
              :get-memory-color="getMemoryColor"
              :get-disk-color="getDiskColor"
              :is-cpu-critical="isCpuCritical"
              :is-memory-critical="isMemoryCritical"
              :is-disk-critical="isDiskCritical"
              :open-metrics-trend="openMetricsTrend"
              :t="t"
            />

            <ServicesGrid
              v-model:service-view-mode="serviceViewMode"
              :is-popout-mode="isPopoutMode"
              :can-operate="canOperate"
              :is-admin="isAdmin"
              :visible-services="visibleServices"
              :controlling="controlling"
              :all-services-running="allServicesRunning"
              :no-services-running="noServicesRunning"
              :batch-control-all="batchControlAll"
              :get-service-border-class="getServiceBorderClass"
              :get-health-bg-class="getHealthBgClass"
              :get-health-state="getHealthState"
              :is-focused-target="isFocusedTarget"
              :drag-state="dragState"
              :service-card-id="serviceCardId"
              :on-drag-start="onDragStart"
              :on-drag-end="onDragEnd"
              :on-drag-over="onDragOver"
              :on-drag-leave="onDragLeave"
              :on-drop="onDrop"
              :get-service-health-text-class="getServiceHealthTextClass"
              :get-service-health-label="getServiceHealthLabel"
              :get-health-tooltip="getHealthTooltip"
              :control-service="controlService"
              :open-service-info="openServiceInfo"
              :open-metrics="openMetrics"
              :load-logs="loadLogs"
              :open-pid-tree="openPidTree"
              :get-service-uptime-display="getServiceUptimeDisplay"
              :service-graph="serviceGraph"
              :service-graph-loading="serviceGraphLoading"
              :is-dark="isDark"
              :popout-workflow="popoutWorkflow"
              :t="t"
            />
          </div>
        </main>

    <CpuCoreDetailsModal
      :cpu-cores-visible="cpuCoresVisible"
      :cpu-core-percents="cpuCorePercents"
      :close-cpu-cores="closeCpuCores"
      :t="t"
    />

    <DiskDetailsModal
      :disk-details-visible="diskDetailsVisible"
      :disk-details="diskDetails"
      :disk-loading="diskLoading"
      :disk-error="diskError"
      :close-disk-details="closeDiskDetails"
      :t="t"
    />

    <ServiceInfoModal
      :service-info-visible="serviceInfoVisible"
      :service-info-loading="serviceInfoLoading"
      :service-info-error="serviceInfoError"
      :service-info="serviceInfo"
      :can-operate="canOperate"
      :handle-update-file-change="handleUpdateFileChange"
      :load-backups="loadBackups"
      :backups-loading="backupsLoading"
      :backups-error="backupsError"
  :backup-options="backupOptions"
  v-model:selected-backup="selectedBackup"
      :rollback-to-selected="rollbackToSelected"
      :uploading-update="uploadingUpdate"
      :updating-service="updatingService"
      :upload-progress="uploadProgress"
      :update-progress="updateProgress"
      :update-status="updateStatus"
      :sched-form="schedForm"
      :current-sched-next="currentSchedNext"
      :weekday-labels="weekdayLabels"
      :toggle-weekday="toggleWeekday"
      :save-scheduled-restart="saveScheduledRestart"
      :format-audit-time="formatAuditTime"
      :close-service-info="closeServiceInfo"
      :t="t"
    />

    <RollbackConfirmModal
      :rollback-confirm-visible="rollbackConfirmVisible"
      :rollback-pending-backup="rollbackPendingBackup"
      :cancel-rollback="cancelRollback"
      :confirm-rollback="confirmRollback"
      :t="t"
    />

    <MetricsViewerModal
      :metrics-service="metricsService"
      :metrics-loading="metricsLoading"
      v-model:metrics-range-hours="metricsRangeHours"
      :get-metrics-points="getMetricsPoints"
      :refresh-metrics-history="refreshMetricsHistory"
      :close-metrics="closeMetrics"
      :t="t"
    />

    <LogViewerModal
      :selected-service="selectedService"
      :log-mode="logMode"
      v-model:log-search="logSearch"
      :log-level-filter="logLevelFilter"
      :log-level-filters="logLevelFilters"
      :log-paused="logPaused"
      :logs-loading="logsLoading"
      :logs="logs"
      :logs-meta="logsMeta"
      :log-file-size="logFileSize"
      :filtered-displayed-logs="filteredDisplayedLogs"
      :search-matches="searchMatches"
      :current-match-index="currentMatchIndex"
      :highlighted-log-line="highlightedLogLine"
      :live-log-limit="LIVE_LOG_LIMIT"
      :set-log-mode="setLogMode"
      :close-log-viewer="closeLogViewer"
      :on-log-level-click="onLogLevelClick"
      :get-log-level-count="getLogLevelCount"
      :toggle-pause="togglePause"
      :remember-current-position="rememberCurrentPosition"
      :go-to-top="goToTop"
      :go-to-bottom="goToBottom"
      :download-logs="downloadLogs"
      :clear-logs="clearLogs"
      :on-logs-scroll="onLogsScroll"
      :get-log-color="getLogColor"
      :is-current-match-line="isCurrentMatchLine"
      :get-log-line-number="getLogLineNumber"
      :on-line-number-click="onLineNumberClick"
      :highlight-log-text="highlightLogText"
      :jump-to-prev-match="jumpToPrevMatch"
      :jump-to-next-match="jumpToNextMatch"
      :format-file-size="formatFileSize"
      :t="t"
    />

    <WebShellTerminal
      :show-terminal="showTerminal"
      v-model:terminal-mode="terminalMode"
      :terminal-connected="terminalConnected"
      :connect-terminal="connectTerminal"
      :close-terminal="closeTerminal"
      :popout-terminal="popoutTerminal"
      :t="t"
    />

    <UserManagementModal
      :show-user-management="showUserManagement"
      :user-list="userList"
      :new-user-form="newUserForm"
      :current-user="currentUser"
      :editing-user-id="editingUserId"
      :show-visible-cards-editor="showVisibleCardsEditor"
      :editing-visible-user="editingVisibleUser"
      :editing-visible-cards="editingVisibleCards"
      :all-card-options="allCardOptions"
      :show-reset-password="showResetPassword"
      :reset-password-user="resetPasswordUser"
      :reset-password-value="resetPasswordValue"
      :create-user="createUser"
      :quick-update-role="quickUpdateRole"
      :open-visible-cards-editor="openVisibleCardsEditor"
      :toggle-visible-card="toggleVisibleCard"
      :save-visible-cards="saveVisibleCards"
      :open-reset-password="openResetPassword"
      :do-reset-password="doResetPassword"
      :delete-user="deleteUser"
      :on-close="() => { showUserManagement = false }"
      :on-close-visible-cards="() => { showVisibleCardsEditor = false }"
      :on-close-reset-password="() => { showResetPassword = false }"
      :on-update-reset-password="(v) => { resetPasswordValue = v }"
      :on-update-editing-visible-cards="(v) => { editingVisibleCards = v }"
      :t="t"
    />

    <AuditLogModal
      :show-audit-log="showAuditLog"
      :filtered-audit-logs="filteredAuditLogs"
      :audit-total="auditTotal"
      :audit-offset="auditOffset"
      :audit-limit="auditLimit"
      :audit-filter="auditFilter"
      :is-admin="isAdmin"
      :load-audit-logs="loadAuditLogs"
      :format-audit-time="formatAuditTime"
      :audit-action-class="auditActionClass"
      :on-close="() => { showAuditLog = false }"
      :t="t"
    />

    <SystemMetricsTrendModal
      :show-metrics-trend="showMetricsTrend"
      :metrics-trend-type="metricsTrendType"
      :trend-range="trendRange"
      :trend-range-options="trendRangeOptions"
      :trend-loading="trendLoading"
      :trend-data="trendData"
      :t="t"
      :on-close="() => { showMetricsTrend = false }"
      :on-select-range="(value) => { trendRange = value; loadMetricsTrend() }"
    />

    <ProcessTreeModal
      :show-pid-tree="showPidTree"
      :pid-tree-service="pidTreeService"
      :pid-tree-data="pidTreeData"
      :pid-tree-loading="pidTreeLoading"
      :can-operate="canOperate"
      :t="t"
      :load-pid-tree="loadPidTree"
      :kill-pid="killPid"
      :format-bytes="formatBytes"
      :format-audit-time="formatAuditTime"
      :on-close="() => { showPidTree = false }"
    />

    <SystemInfoModal
      :visible="showSystemInfo"
      :authorized-fetch="authorizedFetch"
      :t="t"
      @close="showSystemInfo = false"
    />

    <CustomConfirmDialog
      :confirm-dialog="confirmDialog"
      :batch-target-services="batchTargetServices"
      :batch-selected-services="batchSelectedServices"
      :batch-all-selected="batchAllSelected"
      :batch-none-selected="batchNoneSelected"
      :toggle-batch-select-all="toggleBatchSelectAll"
      :toggle-batch-service="toggleBatchService"
      :close-confirm-dialog="closeConfirmDialog"
      :t="t"
    />

    <ToastNotifications :notification="notification" />

    <StatusBar
      v-if="!isPopoutMode"
      :current-user="currentUser"
      :is-admin="isAdmin"
      :is-connected="isConnected"
      :last-updated="lastUpdated"
      :metrics="systemMetrics"
      :on-open-cpu-cores="openCpuCores"
      :on-open-disk-details="openDiskDetails"
      :on-open-system-info="() => { showSystemInfo = true }"
      :on-open-terminal="() => { showTerminal = true }"
      :refresh-status="refreshStatus"
      :t="t"
    />
    </AuthShell>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import SystemMetricsTrendModal from './components/SystemMetricsTrendModal.vue'
import SystemInfoModal from './components/SystemInfoModal.vue'
import CustomConfirmDialog from './components/CustomConfirmDialog.vue'
import ToastNotifications from './components/ToastNotifications.vue'
import StatusBar from './components/StatusBar.vue'
import ProcessTreeModal from './components/ProcessTreeModal.vue'
import CpuCoreDetailsModal from './components/CpuCoreDetailsModal.vue'
import DiskDetailsModal from './components/DiskDetailsModal.vue'
import ServiceInfoModal from './components/ServiceInfoModal.vue'
import RollbackConfirmModal from './components/RollbackConfirmModal.vue'
import MetricsViewerModal from './components/MetricsViewerModal.vue'
import LogViewerModal from './components/LogViewerModal.vue'
import WebShellTerminal from './components/WebShellTerminal.vue'
import UserManagementModal from './components/UserManagementModal.vue'
import AuditLogModal from './components/AuditLogModal.vue'
import LoginScreen from './components/LoginScreen.vue'
import DashboardHeader from './components/DashboardHeader.vue'
import OverviewPanel from './components/OverviewPanel.vue'
import ServicesGrid from './components/ServicesGrid.vue'
import AuthShell from './components/AuthShell.vue'
import { useServiceDisplay } from './composables/useServiceDisplay'
import { useServiceControlUtils } from './composables/useServiceControlUtils'
import { useSessionLifecycle } from './composables/useSessionLifecycle'
import { useServiceControl } from './composables/useServiceControl'
import { useDashboardDisplay } from './composables/useDashboardDisplay'
import { useAuthSession } from './composables/useAuthSession'
import { useApi } from './composables/useApi'
import { useI18n } from './composables/useI18n'
import { useTheme } from './composables/useTheme'
import { useNotification } from './composables/useNotification'
import { useAuth } from './composables/useAuth'
import { useUsers } from './composables/useUsers'
import { useAudit } from './composables/useAudit'
import { useTerminal } from './composables/useTerminal'
import { useDashboard } from './composables/useDashboard'
import { useServices } from './composables/useServices'
import { useLogs } from './composables/useLogs'
import { useMetrics } from './composables/useMetrics'
import { useServiceInfo } from './composables/useServiceInfo'
import { useProcessTree } from './composables/useProcessTree'
import { useStatusAlerts } from './composables/useStatusAlerts'
const { buildApiUrl, buildWsUrl, platformLinkUrl } = useApi()
const { lang, t, langLabel, toggleLanguage } = useI18n()
const { isDark, themeLabel, toggleTheme } = useTheme(t)
const { notification, showNotification, confirmDialog, openConfirmDialog, closeConfirmDialog } = useNotification(t)
let handleUnauthorized = () => {}
const {
  authToken,
  currentUser,
  loginForm,
  loginError,
  loginLoading,
  isAuthenticated,
  userRole,
  isAdmin,
  canOperate,
  authorizedFetch,
  handleLogin,
  logout: baseLogout,
} = useAuth({
  buildApiUrl,
  showNotification,
  t,
  onUnauthorized: () => handleUnauthorized()
})

const {
  showUserManagement,
  userList,
  newUserForm,
  showVisibleCardsEditor,
  editingVisibleUser,
  editingVisibleCards,
  editingUserId,
  showResetPassword,
  resetPasswordUser,
  resetPasswordValue,
  loadUsers,
  createUser,
  quickUpdateRole,
  deleteUser,
  openVisibleCardsEditor,
  toggleVisibleCard,
  saveVisibleCards,
  openResetPassword,
  doResetPassword,
} = useUsers({ authorizedFetch, showNotification, t, currentUser })

const {
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
} = useAudit({ authorizedFetch })

const {
  servicesStatus,
  isPopoutMode,
  serviceViewMode,
  serviceGraph,
  serviceGraphLoading,
  controlling,
  dragState,
  mergeServicesData,
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
} = useServices({ authorizedFetch, showNotification, t, currentUser, openConfirmDialog })

const {
  systemMetrics,
  lastUpdated,
  statusFetchedAt,
  statusTicker,
  isConnected,
  refreshStatus,
  startDashboardSSE,
  startUptimeTicker,
  cleanupDashboard,
} = useDashboard({ authorizedFetch, showNotification, t, servicesStatus, mergeServicesData })

const selectedService = ref(null)
const showSystemInfo = ref(false)

const {
  logs,
  logsLoading,
  logsMeta,
  logFileSize,
  logOffset,
  logHasMorePrev,
  logHasMoreNext,
  logLastPosition,
  searchMatches,
  currentMatchIndex,
  logPaused,
  followLogs,
  highlightedLogLine,
  logSearch,
  logLevelFilter,
  LIVE_LOG_LIMIT,
  logTimeRange,
  logTimeRangeOptions,
  logLevelFilters,
  logMode,
  logLevelCounts,
  getLogLevelCount,
  onLogLevelClick,
  closeLogViewer,
  isCurrentMatchLine,
  getLogLineNumber,
  onLineNumberClick,
  highlightLogText,
  onLogsScroll,
  fetchLogsByLevel,
  cleanupLogsSocket,
  setLogMode,
  displayedLogs,
  filteredDisplayedLogs,
  totalLogs,
  goBackToLastPosition,
  rememberCurrentPosition,
  scrollToLineCenter,
  jumpToLogLine,
  jumpToNextMatch,
  jumpToPrevMatch,
  scrollToSearchMatch,
  loadLogs,
  toRangeQuery,
  fetchMoreLogs,
  togglePause,
  downloadLogs,
  clearLogs,
  getLogColor,
  goToBottom,
  goToTop,
  scrollLogsToBottom,
  scrollLogsToTop,
  formatFileSize,
} = useLogs({
  authorizedFetch,
  buildWsUrl,
  t,
  showNotification,
  selectedService,
  authToken,
  openConfirmDialog,
})

const {
  showTerminal,
  terminalConnected,
  terminalMode,
  connectTerminal,
  openTerminal,
  refitTerminal,
  closeTerminal,
  popoutTerminal,
} = useTerminal({ authToken, buildWsUrl, t })

const {
  metricsService,
  metricsHistory,
  metricsLoading,
  metricsRangeHours,
  showMetricsTrend,
  metricsTrendType,
  trendRange,
  trendData,
  trendLoading,
  trendRangeOptions,
  openMetrics,
  closeMetrics,
  refreshMetricsHistory,
  openMetricsTrend,
  cleanupMetricsStream,
  resetMetricsHistory,
  getMetricsPoints,
  loadMetricsTrend,
} = useMetrics({
  authorizedFetch,
  buildApiUrl,
  showNotification,
  t,
  authToken,
  isDark,
})

const {
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
  uploadingUpdate,
  updatingService,
  uploadProgress,
  updateProgress,
  updateStatus,
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
} = useServiceInfo({
  authorizedFetch,
  buildApiUrl,
  showNotification,
  t,
  authToken,
  servicesStatus,
  lang,
})

const {
  showPidTree,
  pidTreeService,
  pidTreeData,
  pidTreeLoading,
  openPidTree,
  loadPidTree,
  killPid,
  formatBytes,
} = useProcessTree({ authorizedFetch, showNotification, t })

const { isStatusAlertVisible, hideStatusAlert, cleanupStatusAlerts } = useStatusAlerts({
  statusAlerts,
  statusAlertVisibility,
})

const {
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
} = useDashboardDisplay({
  lastUpdated,
  overallHealth,
  overallHealthTextClass,
  systemMetrics,
  isCardVisible,
  t,
})

const { getServiceUptimeDisplay } = useServiceDisplay({ lang, statusFetchedAt })
const { formatControlDetails, schedulePostControlRefresh } = useServiceControlUtils({ refreshStatus })
const { openPlatformLink, cleanupRealtime, handleUnauthorized: sessionHandleUnauthorized } = useSessionLifecycle({
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
})
const { logout, bootstrapSession } = useAuthSession({
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
})
const { controlService } = useServiceControl({
  authorizedFetch,
  showNotification,
  t,
  refreshStatus,
  formatControlDetails,
  schedulePostControlRefresh,
  controlling,
})

handleUnauthorized = sessionHandleUnauthorized

watch(authToken, (token) => {
  if (token) {
    bootstrapSession()
  } else {
    cleanupRealtime()
  }
})

watch(serviceViewMode, (mode) => {
  if (mode === 'topo' || mode === 'force') {
    loadServiceGraph()
  }
})


onMounted(() => {
  applyWorkflowViewFromUrl()
  bootstrapSession()
})

onUnmounted(() => {
  cleanupRealtime()
  cleanupStatusAlerts()
  closeTerminal()
})
</script>
