<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div
        v-if="confirmDialog.show"
        class="fixed inset-0 z-[60] flex items-center justify-center p-4"
        @click.self="closeConfirmDialog(false)"
      >
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        <div class="relative w-full max-w-md transform transition-all">
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-gray-200/80 dark:border-gray-700/60 shadow-2xl overflow-hidden">
            <!-- Icon + Top accent bar -->
            <div
              class="h-1"
              :class="{
                'bg-gradient-to-r from-emerald-400 to-green-500': confirmDialog.type === 'start',
                'bg-gradient-to-r from-red-400 to-rose-500': confirmDialog.type === 'stop' || confirmDialog.type === 'danger',
                'bg-gradient-to-r from-blue-400 to-indigo-500': confirmDialog.type === 'info',
              }"
            ></div>

            <div class="px-6 pt-6 pb-2 text-center">
              <!-- Animated icon -->
              <div
                class="mx-auto mb-4 h-16 w-16 rounded-full flex items-center justify-center"
                :class="{
                  'bg-emerald-100 dark:bg-emerald-500/15': confirmDialog.type === 'start',
                  'bg-red-100 dark:bg-red-500/15': confirmDialog.type === 'stop' || confirmDialog.type === 'danger',
                  'bg-blue-100 dark:bg-blue-500/15': confirmDialog.type === 'info',
                }"
              >
                <!-- Start icon -->
                <svg v-if="confirmDialog.type === 'start'" viewBox="0 0 24 24" class="h-8 w-8 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="6 3 20 12 6 21 6 3" />
                </svg>
                <!-- Stop icon -->
                <svg v-else-if="confirmDialog.type === 'stop' || confirmDialog.type === 'danger'" viewBox="0 0 24 24" class="h-8 w-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <rect x="9" y="9" width="6" height="6" rx="0.5" />
                </svg>
                <!-- Info icon -->
                <svg v-else viewBox="0 0 24 24" class="h-8 w-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </div>

              <!-- Title -->
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">{{ confirmDialog.title }}</h3>

              <!-- Message -->
              <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{{ confirmDialog.message }}</p>

              <!-- Detail / affected count -->
              <div v-if="confirmDialog.detail" class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800/60 text-xs text-gray-600 dark:text-gray-300">
                <svg viewBox="0 0 24 24" class="h-3.5 w-3.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 16h-1v-4h-1" /><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
                {{ confirmDialog.detail }}
              </div>

              <!-- Services list preview (interactive selection) -->
              <div v-if="(confirmDialog.type === 'start' || confirmDialog.type === 'stop') && batchTargetServices.length > 0" class="mt-4">
                <!-- Select all / deselect all header -->
                <div class="flex items-center justify-between mb-2 px-1">
                  <button
                    @click="toggleBatchSelectAll"
                    class="inline-flex items-center gap-1.5 text-[11px] font-medium transition rounded px-1.5 py-0.5"
                    :class="batchAllSelected
                      ? 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                      : (confirmDialog.type === 'start'
                        ? 'text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300'
                        : 'text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300')"
                  >
                    <!-- Checkbox icon -->
                    <svg v-if="batchAllSelected" viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="3" />
                      <path d="M9 12l2 2 4-4" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="3" />
                    </svg>
                    {{ batchAllSelected ? t('batch_deselect_all') : t('batch_select_all') }}
                  </button>
                  <span class="text-[11px] text-gray-400 dark:text-gray-500 tabular-nums">
                    {{ batchSelectedServices.size }}/{{ batchTargetServices.length }}
                  </span>
                </div>
                <!-- Service items -->
                <div class="max-h-40 overflow-y-auto rounded-lg border border-gray-200/60 dark:border-gray-700/40 divide-y divide-gray-100 dark:divide-gray-800/50">
                  <button
                    v-for="s in batchTargetServices"
                    :key="s.name"
                    @click="toggleBatchService(s.name)"
                    class="w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors group"
                    :class="batchSelectedServices.has(s.name)
                      ? (confirmDialog.type === 'start'
                        ? 'bg-emerald-50/60 dark:bg-emerald-500/5 hover:bg-emerald-50 dark:hover:bg-emerald-500/10'
                        : 'bg-red-50/60 dark:bg-red-500/5 hover:bg-red-50 dark:hover:bg-red-500/10')
                      : 'bg-white dark:bg-transparent hover:bg-gray-50 dark:hover:bg-gray-800/30'"
                  >
                    <!-- Custom checkbox -->
                    <span
                      class="flex-shrink-0 h-4 w-4 rounded border-[1.5px] flex items-center justify-center transition-all"
                      :class="batchSelectedServices.has(s.name)
                        ? (confirmDialog.type === 'start'
                          ? 'bg-emerald-500 border-emerald-500 dark:bg-emerald-600 dark:border-emerald-600'
                          : 'bg-red-500 border-red-500 dark:bg-red-600 dark:border-red-600')
                        : 'border-gray-300 dark:border-gray-600 group-hover:border-gray-400 dark:group-hover:border-gray-500'"
                    >
                      <svg v-if="batchSelectedServices.has(s.name)" viewBox="0 0 24 24" class="h-3 w-3 text-white" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </span>
                    <!-- Status dot -->
                    <span
                      class="h-1.5 w-1.5 rounded-full flex-shrink-0"
                      :class="confirmDialog.type === 'start' ? 'bg-amber-400' : 'bg-green-500'"
                    ></span>
                    <!-- Service name -->
                    <span
                      class="text-xs font-mono truncate"
                      :class="batchSelectedServices.has(s.name)
                        ? 'text-gray-800 dark:text-gray-200'
                        : 'text-gray-400 dark:text-gray-500 line-through'"
                    >{{ s.name }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Buttons -->
            <div class="px-6 pb-6 pt-4 flex gap-3">
              <button
                @click="closeConfirmDialog(false)"
                class="flex-1 px-4 py-2.5 text-sm font-medium rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700 transition focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-600"
              >
                {{ confirmDialog.cancelText }}
              </button>
              <button
                @click="closeConfirmDialog(true)"
                :disabled="(confirmDialog.type === 'start' || confirmDialog.type === 'stop') && batchNoneSelected"
                class="flex-1 px-4 py-2.5 text-sm font-medium rounded-xl text-white transition focus:outline-none focus:ring-2 focus:ring-offset-2 inline-flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                :class="{
                  'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500': confirmDialog.type === 'start',
                  'bg-red-600 hover:bg-red-700 focus:ring-red-500': confirmDialog.type === 'stop' || confirmDialog.type === 'danger',
                  'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500': confirmDialog.type === 'info',
                }"
              >
                <svg v-if="confirmDialog.type === 'start'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3" /></svg>
                <svg v-else-if="confirmDialog.type === 'stop' || confirmDialog.type === 'danger'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12" rx="1" /></svg>
                {{ confirmDialog.confirmText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  confirmDialog: { type: Object, required: true },
  batchTargetServices: { type: Array, required: true },
  batchSelectedServices: { type: Object, required: true },
  batchAllSelected: { type: Boolean, required: true },
  batchNoneSelected: { type: Boolean, required: true },
  toggleBatchSelectAll: { type: Function, required: true },
  toggleBatchService: { type: Function, required: true },
  closeConfirmDialog: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
