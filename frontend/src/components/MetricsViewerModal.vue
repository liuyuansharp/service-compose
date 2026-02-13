<template>
  <!-- Metrics Viewer Modal -->
  <div
    v-if="metricsService"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="closeMetrics"
  >
    <div class="tech-card rounded-md w-full max-w-4xl max-h-[92vh] sm:max-h-[90vh] flex flex-col">
      <div class="flex flex-wrap justify-between items-center gap-3 p-4 sm:p-5 border-b border-gray-200 dark:border-slate-800">
        <h3 class="text-base sm:text-xl font-semibold text-gray-900 dark:text-slate-100">
          {{ t('metrics') }} - {{ metricsService }} ({{ t('history') }})
        </h3>
        <div class="flex items-center gap-2">
          <select
            v-model.number="metricsRangeHours"
            class="px-2 py-1 border border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded text-sm"
          >
            <option :value="1">{{ t('range_1h') }}</option>
            <option :value="6">{{ t('range_6h') }}</option>
            <option :value="24">{{ t('range_24h') }}</option>
            <option :value="168">{{ t('range_7d') }}</option>
            <option :value="720">{{ t('range_30d') }}</option>
            <option :value="0">{{ t('range_all') }}</option>
          </select>
          <button
            @click="refreshMetricsHistory"
            class="px-3 py-1 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded text-sm hover:bg-gray-300 dark:hover:bg-gray-700"
          >
            {{ t('refresh') }}
          </button>
          <button
            @click="closeMetrics"
            class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 sm:p-5 bg-gray-50 dark:bg-slate-950">
        <div class="relative">
          <div
            v-if="metricsLoading"
            class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 text-gray-500 dark:text-slate-300 text-center p-8 rounded-md z-10"
          >
            {{ t('loading_metrics') }}
          </div>
          <div :class="['grid grid-cols-1 gap-4 sm:gap-6', metricsLoading ? 'opacity-50 pointer-events-none' : '']">
            <div class="tech-card rounded-md p-4">
              <div class="flex justify-between items-center mb-2">
                <h4 class="font-semibold text-gray-800 dark:text-slate-100">CPU (%)</h4>
                <span class="text-xs text-gray-500 dark:text-slate-400">
                  {{ t('latest') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.cpu_percent ?? 0 }}%
                </span>
              </div>
              <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400 mb-2">
                <span class="flex items-center gap-1">
                  <span class="inline-block w-3 h-3 rounded-full bg-blue-600"></span>CPU
                </span>
              </div>
              <div id="metrics-cpu-chart" class="w-full h-40"></div>
            </div>

            <div class="tech-card rounded-md p-4">
              <div class="flex justify-between items-center mb-2">
                <h4 class="font-semibold text-gray-800 dark:text-slate-100">{{ t('memory') }} (MB)</h4>
                <span class="text-xs text-gray-500 dark:text-slate-400">
                  {{ t('latest') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.memory_mb ?? 0 }} MB
                </span>
              </div>
              <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400 mb-2">
                <span class="flex items-center gap-1">
                  <span class="inline-block w-3 h-3 rounded-full bg-purple-600"></span>{{ t('memory') }}
                </span>
              </div>
              <div id="metrics-memory-chart" class="w-full h-40"></div>
            </div>

            <div class="tech-card rounded-md p-4">
              <div class="flex justify-between items-center mb-2">
                <h4 class="font-semibold text-gray-800 dark:text-slate-100">{{ t('disk_io') }} (MB/s)</h4>
                <span class="text-xs text-gray-500 dark:text-slate-400">
                  {{ t('read') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.read_mb_s ?? 0 }} MB/s
                  · {{ t('write') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.write_mb_s ?? 0 }} MB/s
                </span>
              </div>
              <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400 mb-2">
                <span class="flex items-center gap-1">
                  <span class="inline-block w-3 h-3 rounded-full bg-orange-500"></span>{{ t('read') }}
                </span>
                <span class="flex items-center gap-1">
                  <span class="inline-block w-3 h-3 rounded-full bg-emerald-500"></span>{{ t('write') }}
                </span>
              </div>
              <div id="metrics-disk-chart" class="w-full h-40"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const metricsRangeHours = defineModel('metricsRangeHours', { type: Number, required: true })

defineProps({
  metricsService: { type: [String, null], default: null },
  metricsLoading: { type: Boolean, required: true },
  getMetricsPoints: { type: Function, required: true },
  refreshMetricsHistory: { type: Function, required: true },
  closeMetrics: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
