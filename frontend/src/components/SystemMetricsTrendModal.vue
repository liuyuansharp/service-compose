<template>
  <div
    v-if="showMetricsTrend"
    class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="onClose()"
  >
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="onClose()"></div>
    <div class="relative w-full max-w-4xl max-h-[92vh] sm:max-h-[85vh] flex flex-col bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div
            class="h-9 w-9 rounded-lg flex items-center justify-center"
            :class="metricsTrendType === 'cpu' ? 'bg-blue-100 dark:bg-blue-500/20' : 'bg-purple-100 dark:bg-purple-500/20'"
          >
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5"
              :class="metricsTrendType === 'cpu' ? 'text-blue-600 dark:text-blue-400' : 'text-purple-600 dark:text-purple-400'"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ metricsTrendType === 'cpu' ? t('cpu_trend_title') : t('mem_trend_title') }}
          </h3>
        </div>
        <button @click="onClose()" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-1">
          <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18" /><path d="M6 6l12 12" /></svg>
        </button>
      </div>
      <!-- Time Range Tabs -->
      <div class="px-6 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2 flex-shrink-0 overflow-x-auto">
        <button
          v-for="r in trendRangeOptions"
          :key="r.value"
          @click="onSelectRange(r.value)"
          class="px-3 py-1.5 rounded-md text-xs font-medium transition whitespace-nowrap"
          :class="trendRange === r.value
            ? (metricsTrendType === 'cpu' ? 'bg-blue-600 text-white' : 'bg-purple-600 text-white')
            : 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600'"
        >{{ r.label }}</button>
      </div>
      <!-- Chart Area -->
      <div class="flex-1 p-4 sm:p-6 min-h-0">
        <div v-if="trendLoading" class="h-full flex items-center justify-center text-sm text-gray-400">
          {{ t('loading_info') }}
        </div>
        <div v-else-if="trendData.length === 0" class="h-full flex items-center justify-center text-sm text-gray-400">
          {{ t('trend_no_data') }}
        </div>
        <div v-else id="trend-chart" class="w-full" style="height: min(380px, 50vh);"></div>
      </div>
      <!-- Footer info -->
      <div class="px-6 py-2 border-t border-gray-100 dark:border-gray-800 text-[11px] text-gray-400 dark:text-gray-500 flex-shrink-0">
        {{ t('trend_points', { count: trendData.length }) }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  showMetricsTrend: { type: Boolean, required: true },
  metricsTrendType: { type: String, required: true },
  trendRange: { type: String, required: true },
  trendRangeOptions: { type: Array, required: true },
  trendLoading: { type: Boolean, required: true },
  trendData: { type: Array, required: true },
  t: { type: Function, required: true },
  onClose: { type: Function, required: true },
  onSelectRange: { type: Function, required: true },
})
</script>
