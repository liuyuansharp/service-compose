<template>
  <div
    v-if="showPidTree"
    class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4"
  @click.self="onClose()"
  >
  <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="onClose()"></div>
    <div class="relative w-full max-w-4xl max-h-[92vh] sm:max-h-[85vh] flex flex-col bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-lg bg-indigo-100 dark:bg-indigo-500/20 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="5" r="2.5"/><circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="19" r="2.5"/>
              <path d="M12 7.5v4M12 11.5l-6 5M12 11.5l6 5"/>
            </svg>
          </div>
          <div>
            <h3 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">{{ t('pid_tree_title', { service: pidTreeService }) }}</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('pid_tree_desc') }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="loadPidTree()" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">{{ t('pid_tree_refresh') }}</button>
          <button @click="onClose()" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-1">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
          </button>
        </div>
      </div>
      <div class="flex-1 overflow-y-auto p-4 sm:p-6">
        <div v-if="pidTreeLoading" class="flex items-center justify-center py-12 text-sm text-gray-400">
          <svg class="animate-spin h-5 w-5 mr-2 text-blue-500" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25"/><path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="3" stroke-linecap="round" class="opacity-75"/></svg>
          {{ t('pid_tree_loading') }}
        </div>
        <div v-else-if="!pidTreeData?.flat?.length" class="flex flex-col items-center justify-center py-12 text-sm text-gray-400">
          <svg viewBox="0 0 24 24" class="h-10 w-10 mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><path d="M8 15s1.5-2 4-2 4 2 4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
          {{ t('pid_tree_empty') }}
        </div>
        <div v-else class="space-y-0">
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ t('pid_tree_total', { count: pidTreeData.flat.length }) }}</span>
            <button
              v-if="canOperate && pidTreeData.flat.length > 1"
              @click="killPid(pidTreeData.pid, true)"
              class="px-2.5 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition inline-flex items-center gap-1.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
              {{ t('pid_tree_kill_all') }}
            </button>
          </div>
          <div
            v-for="proc in pidTreeData.flat"
            :key="proc.pid"
            class="relative"
          >
            <div class="flex items-start">
              <div class="flex-shrink-0 flex items-center" :style="{ width: (proc.depth * 24) + 'px' }">
                <template v-if="proc.depth > 0">
                  <span
                    v-for="d in proc.depth"
                    :key="d"
                    class="inline-block w-6 h-full"
                  >
                    <span v-if="d === proc.depth" class="inline-flex items-center h-full">
                      <svg class="h-4 w-6 text-gray-300 dark:text-gray-600" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M0 0 V8 H24"/>
                      </svg>
                    </span>
                  </span>
                </template>
              </div>
              <div :class="[
                'flex-1 rounded-lg border p-3 mb-2 transition',
                proc.depth === 0
                  ? 'border-indigo-300/60 dark:border-indigo-500/30 bg-indigo-50/50 dark:bg-indigo-950/20'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-800/50 hover:border-gray-300 dark:hover:border-gray-600'
              ]">
                <div class="flex items-center justify-between gap-2 flex-wrap">
                  <div class="flex items-center gap-2 flex-wrap min-w-0">
                    <span :class="[
                      'text-[10px] px-1.5 py-0.5 rounded-full font-mono font-semibold flex-shrink-0',
                      proc.depth === 0
                        ? 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 border border-indigo-400/30'
                        : 'bg-gray-500/15 text-gray-600 dark:text-gray-400 border border-gray-300/40 dark:border-gray-600/40'
                    ]">PID {{ proc.pid }}</span>
                    <span class="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">{{ proc.name }}</span>
                    <span :class="[
                      'text-[10px] px-1.5 py-0.5 rounded-full',
                      proc.status === 'running' || proc.status === 'sleeping'
                        ? 'bg-green-500/15 text-green-600 dark:text-green-400'
                        : proc.status === 'zombie'
                        ? 'bg-red-500/15 text-red-600 dark:text-red-400'
                        : 'bg-gray-500/15 text-gray-500'
                    ]">{{ proc.status }}</span>
                    <span v-if="proc.depth === 0" class="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/15 text-indigo-600 dark:text-indigo-400">{{ t('pid_tree_root') }}</span>
                  </div>
                  <button
                    v-if="canOperate"
                    @click="killPid(proc.pid, false)"
                    class="flex-shrink-0 px-2 py-1 bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] rounded hover:bg-red-500/20 transition border border-red-300/30 dark:border-red-500/20 inline-flex items-center gap-1"
                  >
                    <svg viewBox="0 0 24 24" class="h-2.5 w-2.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                    {{ t('pid_tree_kill') }}
                  </button>
                </div>
                <div class="mt-2">
                  <p class="text-[10px] text-gray-400 dark:text-gray-500 mb-0.5">{{ t('pid_tree_cmd') }}</p>
                  <p class="text-[11px] font-mono text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-800 rounded px-2 py-1 break-all leading-relaxed max-h-16 overflow-y-auto">{{ proc.cmdline || '—' }}</p>
                </div>
                <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
                  <span class="text-gray-500 dark:text-gray-400">
                    CPU <span class="font-mono font-semibold" :class="proc.cpu_percent > 80 ? 'text-red-500' : proc.cpu_percent > 50 ? 'text-amber-500' : 'text-blue-600 dark:text-blue-400'">{{ proc.cpu_percent }}%</span>
                  </span>
                  <span class="text-gray-500 dark:text-gray-400">
                    MEM <span class="font-mono font-semibold" :class="proc.memory_percent > 80 ? 'text-red-500' : proc.memory_percent > 50 ? 'text-amber-500' : 'text-purple-600 dark:text-purple-400'">{{ proc.memory_mb }} MB</span>
                    <span class="text-gray-400 dark:text-gray-500">({{ proc.memory_percent }}%)</span>
                  </span>
                  <span class="text-gray-500 dark:text-gray-400">
                    {{ t('pid_tree_read') }} <span class="font-mono text-orange-600 dark:text-orange-400">{{ formatBytes(proc.read_bytes) }}</span>
                  </span>
                  <span class="text-gray-500 dark:text-gray-400">
                    {{ t('pid_tree_write') }} <span class="font-mono text-emerald-600 dark:text-emerald-400">{{ formatBytes(proc.write_bytes) }}</span>
                  </span>
                  <span class="text-gray-500 dark:text-gray-400">
                    {{ t('pid_tree_threads') }} <span class="font-mono text-gray-700 dark:text-gray-300">{{ proc.num_threads }}</span>
                  </span>
                  <span v-if="proc.create_time" class="text-gray-400 dark:text-gray-500">
                    {{ t('pid_tree_created') }} <span class="font-mono">{{ formatAuditTime(proc.create_time) }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  showPidTree: { type: Boolean, required: true },
  pidTreeService: { type: String, required: true },
  pidTreeData: { type: Object, required: true },
  pidTreeLoading: { type: Boolean, required: true },
  onClose: { type: Function, required: true },
  canOperate: { type: Boolean, required: true },
  t: { type: Function, required: true },
  loadPidTree: { type: Function, required: true },
  killPid: { type: Function, required: true },
  formatBytes: { type: Function, required: true },
  formatAuditTime: { type: Function, required: true },
})
</script>
