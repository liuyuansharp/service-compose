<template>
  <div
    v-show="selectedService"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="closeLogViewer"
  >
    <div class="tech-card rounded-lg w-full max-w-4xl max-h-[92vh] sm:max-h-[90vh] flex flex-col overflow-hidden">
      <!-- ═══ Header ═══ -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80">
        <div class="flex items-center gap-3 min-w-0">
          <div class="h-8 w-8 rounded-lg flex items-center justify-center flex-shrink-0"
            :class="logMode === 'live' ? 'bg-emerald-100 dark:bg-emerald-500/20' : 'bg-slate-100 dark:bg-slate-700/40'">
            <svg v-if="logMode === 'live'" viewBox="0 0 24 24" class="h-4 w-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" class="h-4 w-4 text-slate-600 dark:text-slate-300" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="min-w-0">
            <h3 class="text-sm sm:text-base font-semibold text-gray-900 dark:text-slate-100 truncate">{{ selectedService }}</h3>
            <p class="text-[10px] text-gray-500 dark:text-gray-400">{{ logMode === 'live' ? t('log_mode_live_desc') : t('log_mode_history_desc') }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <div class="flex bg-gray-200/80 dark:bg-gray-800/80 rounded-md p-0.5">
            <button
              @click.prevent="setLogMode('live')"
              class="px-2.5 py-1 rounded text-[11px] font-semibold transition-all inline-flex items-center gap-1"
              :class="logMode === 'live'
                ? 'bg-emerald-500 text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
            >
              <span class="relative flex h-1.5 w-1.5" v-if="logMode === 'live'">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-white"></span>
              </span>
              {{ t('log_mode_live') }}
            </button>
            <button
              @click.prevent="setLogMode('history')"
              class="px-2.5 py-1 rounded text-[11px] font-semibold transition-all inline-flex items-center gap-1"
              :class="logMode === 'history'
                ? 'bg-slate-700 text-white shadow-sm dark:bg-slate-500'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
            >
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              {{ t('log_mode_history') }}
            </button>
          </div>
          <button @click="closeLogViewer" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-1 transition">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
          </button>
        </div>
      </div>

      <!-- ═══ Toolbar ═══ -->
      <div class="flex items-center gap-2 px-3 py-1.5 border-b border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-950">
        <div class="flex items-center gap-0.5 bg-gray-200/60 dark:bg-gray-800/60 rounded-md p-0.5 flex-shrink-0">
          <button
            v-for="lvl in logLevelFilters"
            :key="lvl.value"
            @click="onLogLevelClick(lvl.value)"
            class="px-1.5 py-1 rounded text-[10px] font-semibold transition leading-none"
            :class="logLevelFilter === lvl.value
              ? lvl.activeClass
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
          >
            {{ typeof lvl.label === 'object' ? lvl.label.value : lvl.label }}
            <span v-if="lvl.value !== 'ALL'" class="ml-0.5 opacity-70 tabular-nums">{{ getLogLevelCount(lvl.value) }}</span>
          </button>
        </div>

        <div class="flex-1 min-w-0 flex gap-1 items-center">
          <div class="relative flex-1 min-w-0">
            <svg viewBox="0 0 24 24" class="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="logSearch"
              type="text"
              :placeholder="`${t('search_logs')}...`"
              class="w-full pl-7 pr-7 py-1 border border-gray-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              v-if="logSearch"
              @click="logSearch = ''"
              class="absolute right-1.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              :title="t('clear')"
            >
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
            </button>
          </div>
          <template v-if="logSearch && searchMatches[selectedService]?.length">
            <span class="text-[10px] text-gray-400 tabular-nums whitespace-nowrap">{{ (currentMatchIndex[selectedService] ?? -1) + 1 }}/{{ searchMatches[selectedService].length }}</span>
            <button @click="jumpToPrevMatch" class="p-0.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition" :title="t('prev')">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            <button @click="jumpToNextMatch" class="p-0.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition" :title="t('next')">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </template>
        </div>

        <div class="w-px h-5 bg-gray-300 dark:bg-gray-700 flex-shrink-0"></div>

        <div class="flex items-center gap-1 flex-shrink-0">
          <button
            v-if="logMode === 'live'"
            @click="togglePause"
            class="px-2 py-1 rounded text-[10px] font-semibold transition inline-flex items-center gap-1"
            :class="logPaused
              ? 'bg-emerald-500/90 text-white hover:bg-emerald-600'
              : 'bg-amber-500/90 text-white hover:bg-amber-600'"
            :title="logPaused ? t('resume') : t('pause')"
          >
            <svg v-if="logPaused" viewBox="0 0 24 24" class="h-3 w-3" fill="currentColor"><polygon points="5 3 19 12 5 21"/></svg>
            <svg v-else viewBox="0 0 24 24" class="h-3 w-3" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
            {{ logPaused ? t('resume') : t('pause') }}
          </button>
          <button
            @click="() => { rememberCurrentPosition(); goToTop() }"
            class="p-1 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
            :title="t('top')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/><line x1="6" y1="5" x2="18" y2="5"/></svg>
          </button>
          <button
            @click="() => { rememberCurrentPosition(); goToBottom() }"
            class="p-1 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
            :title="t('bottom')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/><line x1="6" y1="19" x2="18" y2="19"/></svg>
          </button>
          <button
            @click="downloadLogs"
            class="p-1 rounded text-gray-500 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition"
            :title="t('download')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </button>
          <button
            v-if="logMode === 'live'"
            @click="clearLogs"
            class="p-1 rounded text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
            :title="t('clear')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>

      <!-- ═══ Body ═══ -->
      <div
        :ref="(el) => { if (logsContainerRef) logsContainerRef.value = el }"
        class="flex-1 overflow-y-auto bg-[#0d1117] font-mono text-xs leading-5"
        style="min-height: 200px"
        @scroll="onLogsScroll"
      >
        <div v-if="logsLoading[selectedService]" class="text-gray-400 text-center py-12 flex flex-col items-center gap-2">
          <svg class="animate-spin h-5 w-5 text-blue-400" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25"/><path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="3" stroke-linecap="round" class="opacity-75"/></svg>
          <span>{{ t('loading_logs') }}...</span>
        </div>
        <div v-else-if="filteredDisplayedLogs.length === 0" class="text-gray-500 text-center py-12">
          <svg viewBox="0 0 24 24" class="h-8 w-8 mx-auto mb-2 text-gray-600" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
          <p>{{ t('no_logs_available') }}</p>
          <p v-if="logLevelFilter !== 'ALL'" class="text-xs mt-1 text-gray-600">{{ t('log_filter_no_match') }}</p>
        </div>
        <div v-else class="px-2 py-1">
          <div
            v-for="(log, idx) in filteredDisplayedLogs"
            :key="log._fIdx"
            :data-line="log.line"
            class="flex hover:bg-white/5 rounded-sm transition-colors"
            :class="[
              getLogColor(log.level),
              isCurrentMatchLine(log, idx) ? 'bg-yellow-500/15 ring-1 ring-yellow-500/40' : '',
              highlightedLogLine && log.line === highlightedLogLine ? 'log-line-highlight' : ''
            ]"
          >
            <span
              class="text-gray-600 select-none w-12 sm:w-14 text-right pr-2 border-r border-gray-800/60 text-[10px] flex-shrink-0 leading-5 cursor-pointer hover:text-blue-400 transition-colors tabular-nums"
              @click="onLineNumberClick(log)"
            >{{ getLogLineNumber(log) }}</span>
            <span
              class="mx-1 text-[9px] font-bold w-6 text-center flex-shrink-0 leading-5 rounded-sm"
              :class="{
                'text-red-400 bg-red-500/10': log.level === 'ERROR',
                'text-yellow-400 bg-yellow-500/10': log.level === 'WARNING',
                'text-green-500 bg-green-500/5': log.level === 'INFO',
                'text-blue-400 bg-blue-500/10': log.level === 'DEBUG',
                'text-gray-500': !['ERROR','WARNING','INFO','DEBUG'].includes(log.level)
              }"
            >{{ log.level?.charAt(0) || '—' }}</span>
            <span class="pl-1 flex-1 leading-5 whitespace-pre-wrap break-all" v-html="highlightLogText(log.raw)"></span>
          </div>
        </div>
      </div>

      <!-- ═══ Footer ═══ -->
      <div class="px-3 py-1.5 border-t border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-950 text-[10px] text-gray-500 dark:text-slate-400 flex items-center gap-2 flex-wrap">
        <span v-if="logMode === 'live'" class="inline-flex items-center gap-1">
          <span class="relative flex h-1.5 w-1.5">
            <span v-if="!logPaused" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-1.5 w-1.5" :class="logPaused ? 'bg-amber-400' : 'bg-emerald-400'"></span>
          </span>
          <span :class="logPaused ? 'text-amber-500' : 'text-emerald-500'" class="font-medium">{{ logPaused ? t('paused') : t('streaming') }}</span>
        </span>
        <span class="tabular-nums">{{ t('showing_logs', { count: filteredDisplayedLogs.length }) }}</span>
        <span v-if="logLevelFilter !== 'ALL'" class="px-1 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-medium">
          {{ logLevelFilter }}
        </span>
        <span v-if="logSearch && searchMatches[selectedService]?.length" class="text-yellow-500">
          {{ t('match') }}: {{ searchMatches[selectedService].length }}
        </span>
        <span class="flex-1"></span>
        <span v-if="logMode === 'history' && selectedService && logsMeta[selectedService]" class="tabular-nums">
          {{ t('total_lines', { count: logsMeta[selectedService].total }) }}
        </span>
        <span v-if="logMode === 'history' && selectedService && logFileSize[selectedService] != null" class="tabular-nums text-gray-400 dark:text-gray-500">
          ({{ formatFileSize(logFileSize[selectedService]) }})
        </span>
        <span v-if="logMode === 'live'" class="tabular-nums">
          {{ t('buffer_size', { count: (logs[selectedService] || []).length, max: liveLogLimit }) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
const logSearch = defineModel('logSearch', { type: String, required: true })

defineProps({
  selectedService: { type: [String, null], default: null },
  logMode: { type: String, required: true },
  logLevelFilter: { type: String, required: true },
  logLevelFilters: { type: Array, required: true },
  logPaused: { type: Boolean, required: true },
  logsLoading: { type: Object, required: true },
  logs: { type: Object, required: true },
  logsMeta: { type: Object, required: true },
  logFileSize: { type: Object, required: true },
  filteredDisplayedLogs: { type: Array, required: true },
  searchMatches: { type: Object, required: true },
  currentMatchIndex: { type: Object, required: true },
  highlightedLogLine: { type: [Number, null], default: null },
  liveLogLimit: { type: Number, required: true },
  logsContainerRef: { type: Object, default: null },
  setLogMode: { type: Function, required: true },
  closeLogViewer: { type: Function, required: true },
  onLogLevelClick: { type: Function, required: true },
  getLogLevelCount: { type: Function, required: true },
  togglePause: { type: Function, required: true },
  rememberCurrentPosition: { type: Function, required: true },
  goToTop: { type: Function, required: true },
  goToBottom: { type: Function, required: true },
  downloadLogs: { type: Function, required: true },
  clearLogs: { type: Function, required: true },
  onLogsScroll: { type: Function, required: true },
  getLogColor: { type: Function, required: true },
  isCurrentMatchLine: { type: Function, required: true },
  getLogLineNumber: { type: Function, required: true },
  onLineNumberClick: { type: Function, required: true },
  highlightLogText: { type: Function, required: true },
  jumpToPrevMatch: { type: Function, required: true },
  jumpToNextMatch: { type: Function, required: true },
  formatFileSize: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
