<template>
  <div>
    <div
      v-if="hasCriticalAlert && !isPopoutMode"
      class="mb-4 rounded-md border border-red-300 dark:border-red-500/40 bg-red-50 dark:bg-red-950/40 px-4 py-2 text-sm text-red-700 dark:text-red-200"
    >
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="inline-flex h-2.5 w-2.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"></span>
          <span class="font-semibold">{{ t('alert_title') }}</span>
          <span class="opacity-80">{{ t('alert_metrics') }}</span>
        </div>
        <div class="text-xs font-medium">
          {{ criticalItems.join(' / ') }}
        </div>
      </div>
    </div>

    <div v-if="isCardVisible('overview') && !isPopoutMode" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4 mb-6">
      <div class="tech-card rounded-md p-4 border-l-4" :class="overallStatusBorder">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs font-medium">{{ t('overall_status') }}</p>
            <p class="text-2xl font-semibold mt-2 flex items-center gap-2" :class="statusColor">
              <span>{{ overallHealthLabel }}</span>
              <span
                v-if="overallHealth === 'abnormal'"
                class="inline-flex h-2 w-2 rounded-full bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.6)]"
                :title="overallHealthTooltip"
              ></span>
            </p>
          </div>
          <div class="h-10 w-10 rounded-xl border border-blue-200/70 dark:border-blue-400/30 bg-blue-100/60 dark:bg-blue-500/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 12h6l2-3 2 6 2-3h4" />
            </svg>
          </div>
        </div>
      </div>

      <div class="tech-card rounded-md p-4 border-l-4 border-purple-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs font-medium">{{ t('active_services') }}</p>
            <p class="text-2xl font-semibold text-purple-600 mt-2">
              {{ runningCount }}/{{ servicesStatus.length }}
            </p>
          </div>
          <div class="h-10 w-10 rounded-xl border border-purple-200/70 dark:border-purple-400/30 bg-purple-100/60 dark:bg-purple-500/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="5" y="6" width="14" height="12" rx="2" />
              <path d="M8 10h8" />
              <path d="M8 14h5" />
            </svg>
          </div>
        </div>
      </div>

      <div class="tech-card rounded-md p-4 border-l-4 border-green-500">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs font-medium">{{ t('last_updated') }}</p>
            <p class="text-sm font-mono text-green-600 mt-2">
              {{ formattedTimestamp }}
            </p>
          </div>
          <div class="h-10 w-10 rounded-xl border border-emerald-200/70 dark:border-emerald-400/30 bg-emerald-100/60 dark:bg-emerald-500/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="8" />
              <path d="M12 8v4l3 3" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!isPopoutMode" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4 mb-6">
      <div class="tech-card rounded-md p-4 border-t-4 border-blue-500">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-gray-900 dark:text-slate-100">{{ t('cpu_usage') }}</h3>
          <span class="h-8 w-8 rounded-xl border border-blue-200/60 dark:border-blue-500/30 bg-blue-100/60 dark:bg-blue-500/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14" />
              <path d="M7 8h10" />
              <path d="M9 16h6" />
            </svg>
          </span>
        </div>
        <div class="flex items-center justify-between">
          <div>
            <p :class="getCpuColor" class="text-3xl font-semibold">
              {{ systemMetrics.cpu_percent }}%
            </p>
            <div class="flex items-center gap-2 mt-2">
              <p class="text-xs text-gray-600 dark:text-slate-400">{{ systemMetrics.cpu_count }} {{ t('cores') }}</p>
              <button @click="openCpuCores" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                {{ t('core_usage') }}
              </button>
              <span class="text-gray-300 dark:text-gray-600">|</span>
              <button
                @click="openMetricsTrend('cpu')"
                class="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-0.5"
              >
                <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                {{ t('trend') }}
              </button>
            </div>
          </div>
          <div
            class="w-16 h-16 rounded-full border-4"
            :class="[
              systemMetrics.cpu_percent < 50 ? 'border-green-500' : systemMetrics.cpu_percent < 80 ? 'border-yellow-500' : 'border-red-500',
              isCpuCritical ? 'ring-2 ring-red-400/70 ring-offset-2 ring-offset-white dark:ring-offset-slate-900' : '',
            ]"
            style="display: flex; align-items: center; justify-content: center;"
          >
            <svg class="w-12 h-12" :class="getCpuColor" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                :stroke-dasharray="251.2 * systemMetrics.cpu_percent / 100 + ' 251.2'"
                transform="rotate(-90 50 50)"
                style="transition: all 0.3s ease;"
              />
            </svg>
          </div>
        </div>
      </div>

      <div class="tech-card rounded-md p-4 border-t-4 border-purple-500">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-gray-900 dark:text-slate-100">{{ t('memory_usage') }}</h3>
          <span class="h-8 w-8 rounded-xl border border-purple-200/60 dark:border-purple-500/30 bg-purple-100/60 dark:bg-purple-500/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 7h14" />
              <path d="M5 12h10" />
              <path d="M5 17h7" />
            </svg>
          </span>
        </div>
        <div class="flex items-center justify-between">
          <div>
            <p :class="getMemoryColor" class="text-3xl font-semibold">
              {{ systemMetrics.memory_percent }}%
            </p>
            <p class="text-xs text-gray-600 dark:text-slate-400 mt-2">
              {{ systemMetrics.memory_used }} / {{ systemMetrics.memory_total }} MB
            </p>
            <button
              @click="openMetricsTrend('memory')"
              class="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-0.5 mt-1"
            >
              <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              {{ t('trend') }}
            </button>
          </div>
          <div
            class="w-16 h-16 rounded-full border-4"
            :class="[
              systemMetrics.memory_percent < 50 ? 'border-green-500' : systemMetrics.memory_percent < 80 ? 'border-yellow-500' : 'border-red-500',
              isMemoryCritical ? 'ring-2 ring-red-400/70 ring-offset-2 ring-offset-white dark:ring-offset-slate-900' : '',
            ]"
            style="display: flex; align-items: center; justify-content: center;"
          >
            <svg class="w-12 h-12" :class="getMemoryColor" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                :stroke-dasharray="251.2 * systemMetrics.memory_percent / 100 + ' 251.2'"
                transform="rotate(-90 50 50)"
                style="transition: all 0.3s ease;"
              />
            </svg>
          </div>
        </div>
      </div>

      <div class="tech-card rounded-md p-4 border-t-4 border-orange-500">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-gray-900 dark:text-slate-100">{{ t('disk_usage') }}</h3>
          <span class="h-8 w-8 rounded-xl border border-amber-200/70 dark:border-amber-500/30 bg-amber-100/60 dark:bg-amber-500/10 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 14h16" />
              <path d="M6 10h12" />
              <path d="M8 6h8" />
            </svg>
          </span>
        </div>
        <div class="flex items-center justify-between">
          <div>
            <p :class="getDiskColor" class="text-3xl font-semibold">
              {{ systemMetrics.disk_percent }}%
            </p>
            <p class="text-xs text-gray-600 dark:text-slate-400 mt-2">
              {{ systemMetrics.disk_used }} / {{ systemMetrics.disk_total }} GB
            </p>
            <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ t('disk_free') }}: {{ systemMetrics.disk_free }} GB</p>
            <button @click="openDiskDetails" class="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline">
              {{ t('disk_details') }}
            </button>
          </div>
          <div
            class="w-16 h-16 rounded-full border-4"
            :class="[
              systemMetrics.disk_percent < 50 ? 'border-green-500' : systemMetrics.disk_percent < 80 ? 'border-yellow-500' : 'border-red-500',
              isDiskCritical ? 'ring-2 ring-red-400/70 ring-offset-2 ring-offset-white dark:ring-offset-slate-900' : '',
            ]"
            style="display: flex; align-items: center; justify-content: center;"
          >
            <svg class="w-12 h-12" :class="getDiskColor" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                :stroke-dasharray="251.2 * systemMetrics.disk_percent / 100 + ' 251.2'"
                transform="rotate(-90 50 50)"
                style="transition: all 0.3s ease;"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isPopoutMode: { type: Boolean, required: true },
  hasCriticalAlert: { type: Boolean, required: true },
  criticalItems: { type: Array, required: true },
  isCardVisible: { type: Function, required: true },
  overallStatusBorder: { type: String, required: true },
  statusColor: { type: String, required: true },
  overallHealthLabel: { type: String, required: true },
  overallHealth: { type: String, required: true },
  overallHealthTooltip: { type: String, required: true },
  runningCount: { type: Number, required: true },
  servicesStatus: { type: Array, required: true },
  formattedTimestamp: { type: String, required: true },
  systemMetrics: { type: Object, required: true },
  getCpuColor: { type: String, required: true },
  getMemoryColor: { type: String, required: true },
  getDiskColor: { type: String, required: true },
  isCpuCritical: { type: Boolean, required: true },
  isMemoryCritical: { type: Boolean, required: true },
  isDiskCritical: { type: Boolean, required: true },
  openCpuCores: { type: Function, required: true },
  openMetricsTrend: { type: Function, required: true },
  openDiskDetails: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
