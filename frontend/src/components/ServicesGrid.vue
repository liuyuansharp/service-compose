<template>
  <div :class="isPopoutMode ? '' : 'mb-6'">
    <div v-if="!isPopoutMode" class="flex items-center justify-between mb-3 flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('services') }}</h2>
        <span class="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-[10px] font-bold rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
          {{ visibleServices.length }}
        </span>
      </div>

      <div class="flex items-center gap-1.5">
        <div class="inline-flex items-center rounded-md border border-slate-200/60 dark:border-slate-700/40 bg-white/60 dark:bg-slate-800/40 p-0.5">
          <button
            @click="serviceViewMode = 'list'"
            class="p-1.5 rounded transition"
            :class="serviceViewMode === 'list'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-700/40'"
            :title="t('list_view')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
          </button>
          <button
            @click="serviceViewMode = 'workflow'"
            class="p-1.5 rounded transition"
            :class="serviceViewMode === 'workflow'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-700/40'"
            :title="t('workflow_view')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="5" cy="12" r="2" /><circle cx="19" cy="6" r="2" /><circle cx="19" cy="18" r="2" />
              <path d="M7 12h4l2-6h4" /><path d="M13 12l-2 6h4" />
            </svg>
          </button>
        </div>

        <div v-if="canOperate && visibleServices.length > 1" class="w-px h-5 bg-slate-200 dark:bg-slate-700/60 mx-0.5"></div>

        <div v-if="canOperate && visibleServices.length > 1" class="inline-flex items-center rounded-md border border-slate-200/60 dark:border-slate-700/40 bg-white/60 dark:bg-slate-800/40 p-0.5 gap-0.5">
          <button
            @click="batchControlAll('start')"
            :disabled="controlling || allServicesRunning"
            class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded transition
                   text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/30
                   disabled:opacity-35 disabled:cursor-not-allowed"
            :title="t('batch_start_all')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3" /></svg>
            <span class="hidden sm:inline">{{ t('batch_start_all') }}</span>
          </button>
          <div class="w-px h-4 bg-slate-200 dark:bg-slate-700/60"></div>
          <button
            @click="batchControlAll('stop')"
            :disabled="controlling || noServicesRunning"
            class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded transition
                   text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30
                   disabled:opacity-35 disabled:cursor-not-allowed"
            :title="t('batch_stop_all')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1" /></svg>
            <span class="hidden sm:inline">{{ t('batch_stop_all') }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-show="serviceViewMode === 'list' && !isPopoutMode" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      <div
        v-for="service in visibleServices"
        :key="service.name"
        :id="serviceCardId(service.name)"
        draggable="true"
        @dragstart="onDragStart($event, service.name)"
        @dragend="onDragEnd"
        @dragover="onDragOver($event, service.name)"
        @dragleave="onDragLeave($event, service.name)"
        @drop="onDrop($event, service.name)"
        class="tech-card rounded-md p-3 sm:p-4 transition service-draggable"
        :class="[
          getServiceBorderClass(service),
          getHealthBgClass(getHealthState(service)),
          isFocusedTarget(`service:${service.name}`) ? 'service-focus' : '',
          dragState.over === service.name && dragState.dragging !== service.name ? 'drag-over' : '',
        ]"
      >
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-base font-semibold text-gray-900 dark:text-slate-100">{{ service.name }}</h3>
            <p class="text-xs flex items-center gap-1" :class="getServiceHealthTextClass(service)">
              <span>{{ getServiceHealthLabel(service) }}</span>
              <span
                v-if="getHealthState(service) === 'abnormal'"
                class="inline-flex h-1.5 w-1.5 rounded-full bg-yellow-400 shadow-[0_0_6px_rgba(250,204,21,0.6)]"
                :title="getHealthTooltip(service)"
              ></span>
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-if="service.running && canOperate"
              @click="controlService('stop', service.name)"
              class="px-2.5 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition inline-flex items-center gap-1.5 glass-button-solid"
              :disabled="controlling"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              {{ t('stop') }}
            </button>
            <button
              v-else-if="!service.running && canOperate"
              @click="controlService('start', service.name)"
              class="px-2.5 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition inline-flex items-center gap-1.5 glass-button-solid"
              :disabled="controlling"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 6l10 6-10 6z" />
              </svg>
              {{ t('start') }}
            </button>
            <button
              @click="openServiceInfo(service.name)"
              class="px-2.5 py-1 bg-slate-600 text-white rounded text-xs hover:bg-slate-700 transition inline-flex items-center gap-1.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 10v6" />
                <path d="M12 7h.01" />
              </svg>
              {{ t('info') }}
            </button>
            <button
              @click="openMetrics(service.name)"
              class="px-2.5 py-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700 transition inline-flex items-center gap-1.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 18V6" />
                <path d="M4 18h16" />
                <path d="M7 14l4-4 3 3 5-6" />
              </svg>
              {{ t('metrics') }}
            </button>
            <button
              @click="loadLogs(service.name)"
              class="px-2.5 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition inline-flex items-center gap-1.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 4h7l4 4v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" />
                <path d="M9 12h6" />
                <path d="M9 16h6" />
              </svg>
              {{ t('logs') }}
            </button>
          </div>
        </div>

        <div class="space-y-3">
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">PID</p>
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <p class="text-xs font-mono dark:text-slate-200">{{ service.pid || '—' }}</p>
                <button
                  v-if="service.pid"
                  @click="openPidTree(service.name)"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-300/40 dark:border-blue-500/30 hover:bg-blue-500/25 transition inline-flex items-center gap-0.5"
                  :title="t('pid_tree')"
                >
                  <svg viewBox="0 0 24 24" class="h-2.5 w-2.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="19" r="2"/>
                    <path d="M12 7v4M12 11l-6 6M12 11l6 6"/>
                  </svg>
                  {{ t('pid_tree') }}
                </button>
              </div>
              <p class="text-[11px] text-gray-500 dark:text-slate-400">{{ t('uptime') }}: {{ getServiceUptimeDisplay(service) }}</p>
            </div>
          </div>
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">{{ t('last_log') }}</p>
            <p class="text-xs font-mono text-gray-700 dark:text-slate-300 truncate">
              {{ service.last_log || t('no_logs_yet') }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div v-show="serviceViewMode === 'workflow' || isPopoutMode" :class="isPopoutMode ? '' : 'mt-3'">
      <WorkflowView
        :graph="serviceGraph"
        :services="visibleServices"
        :dark="isDark"
        :is-popout="isPopoutMode"
        :can-operate="canOperate"
        :controlling="controlling"
        :empty-label="serviceGraphLoading ? t('workflow_loading') : t('workflow_empty')"
        :start-label="t('start')"
        :stop-label="t('stop')"
        :info-label="t('info')"
        :metrics-label="t('metrics')"
        :logs-label="t('logs')"
        :uptime-label="t('uptime') || 'Uptime'"
        :topo-label="t('workflow_topo')"
        :force-label="t('workflow_force')"
        :popout-label="t('workflow_popout')"
        :pid-tree-label="t('pid_tree')"
        :last-log-label="t('last_log')"
        :no-logs-label="t('no_logs_yet')"
        :get-health-state="getHealthState"
        :get-service-health-label="getServiceHealthLabel"
        :get-service-health-text-class="getServiceHealthTextClass"
        :get-service-border-class="getServiceBorderClass"
        :get-health-bg-class="getHealthBgClass"
        :get-service-uptime-display="getServiceUptimeDisplay"
        @control="controlService"
        @open-info="openServiceInfo"
        @open-metrics="openMetrics"
        @open-logs="loadLogs"
        @open-pid-tree="openPidTree"
        @popout="popoutWorkflow"
      />
    </div>
  </div>
</template>

<script setup>
import WorkflowView from './WorkflowView.vue'

const serviceViewMode = defineModel('serviceViewMode', { type: String, required: true })

defineProps({
  isPopoutMode: { type: Boolean, required: true },
  canOperate: { type: Boolean, required: true },
  visibleServices: { type: Array, required: true },
  controlling: { type: Boolean, required: true },
  allServicesRunning: { type: Boolean, required: true },
  noServicesRunning: { type: Boolean, required: true },
  batchControlAll: { type: Function, required: true },
  getServiceBorderClass: { type: Function, required: true },
  getHealthBgClass: { type: Function, required: true },
  getHealthState: { type: Function, required: true },
  isFocusedTarget: { type: Function, required: true },
  dragState: { type: Object, required: true },
  serviceCardId: { type: Function, required: true },
  onDragStart: { type: Function, required: true },
  onDragEnd: { type: Function, required: true },
  onDragOver: { type: Function, required: true },
  onDragLeave: { type: Function, required: true },
  onDrop: { type: Function, required: true },
  getServiceHealthTextClass: { type: Function, required: true },
  getServiceHealthLabel: { type: Function, required: true },
  getHealthTooltip: { type: Function, required: true },
  controlService: { type: Function, required: true },
  openServiceInfo: { type: Function, required: true },
  openMetrics: { type: Function, required: true },
  loadLogs: { type: Function, required: true },
  openPidTree: { type: Function, required: true },
  getServiceUptimeDisplay: { type: Function, required: true },
  serviceGraph: { type: Object, required: true },
  serviceGraphLoading: { type: Boolean, required: true },
  isDark: { type: Boolean, required: true },
  popoutWorkflow: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
