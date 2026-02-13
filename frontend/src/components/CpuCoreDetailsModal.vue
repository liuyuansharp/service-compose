<template>
  <!-- CPU Core Details Modal -->
  <div
    v-if="cpuCoresVisible"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="closeCpuCores"
  >
    <div class="tech-card rounded-md w-full max-w-4xl max-h-[90vh] sm:max-h-[85vh] flex flex-col">
      <div class="flex justify-between items-center p-4 sm:p-5 border-b border-gray-200 dark:border-slate-800">
        <div>
          <h3 class="text-lg sm:text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('cpu_cores') }}</h3>
          <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ t('core_usage') }}</p>
        </div>
        <button
          @click="closeCpuCores"
          class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl leading-none"
        >
          ✕
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-4 sm:p-5 bg-gray-50 dark:bg-slate-950">
        <div v-if="!cpuCorePercents.length" class="text-sm text-gray-500 dark:text-slate-400 text-center py-10">
          {{ t('no_core_data') }}
        </div>
        <template v-else>
          <!-- Summary bar -->
          <div class="flex flex-wrap items-center gap-4 sm:gap-6 mb-4 px-1">
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-slate-400">{{ t('core') }}:</span>
              <span class="text-sm font-semibold text-gray-800 dark:text-slate-200">{{ cpuCorePercents.length }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-slate-400">{{ t('cpu_avg') }}:</span>
              <span class="text-sm font-semibold" :class="coreColor(avgPercent)">{{ avgPercent.toFixed(1) }}%</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-slate-400">{{ t('cpu_max') }}:</span>
              <span class="text-sm font-semibold" :class="coreColor(maxPercent)">{{ maxPercent.toFixed(1) }}%</span>
            </div>
            <!-- Overall bar -->
            <div class="flex-1 min-w-[120px] flex items-center gap-2">
              <div class="flex-1 h-2 rounded-full bg-gray-200 dark:bg-slate-800 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :class="barBg(avgPercent)"
                  :style="{ width: `${Math.min(avgPercent, 100)}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Core grid -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div
              v-for="(percent, idx) in cpuCorePercents"
              :key="idx"
              class="tech-card rounded-lg p-3 flex flex-col items-center gap-2 group hover:ring-1 transition-all"
              :class="percent >= 90
                ? 'hover:ring-red-400/50'
                : percent >= 80
                  ? 'hover:ring-amber-400/50'
                  : 'hover:ring-blue-400/50'"
            >
              <!-- Ring chart -->
              <div class="relative w-14 h-14">
                <svg viewBox="0 0 44 44" class="w-full h-full -rotate-90">
                  <circle cx="22" cy="22" r="18" fill="none"
                    class="stroke-gray-200 dark:stroke-slate-700/80" stroke-width="4" />
                  <circle cx="22" cy="22" r="18" fill="none"
                    :class="ringStroke(percent)"
                    stroke-width="4"
                    stroke-linecap="round"
                    :stroke-dasharray="`${Math.min(percent, 100) * 1.131} 113.1`"
                    class="transition-all duration-500"
                  />
                </svg>
                <span class="absolute inset-0 flex items-center justify-center text-[11px] font-bold"
                  :class="coreColor(percent)"
                >{{ Number(percent).toFixed(0) }}%</span>
              </div>
              <!-- Label -->
              <div class="text-center">
                <div class="text-[11px] font-mono text-gray-600 dark:text-slate-300">{{ t('core') }} {{ idx + 1 }}</div>
                <div class="text-[10px] font-medium mt-0.5"
                  :class="coreColor(percent)"
                >{{ percent >= 90 ? t('core_level_high') : percent >= 80 ? t('core_level_mid') : t('core_level_low') }}</div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  cpuCoresVisible: { type: Boolean, required: true },
  cpuCorePercents: { type: Array, required: true },
  closeCpuCores: { type: Function, required: true },
  t: { type: Function, required: true },
})

const avgPercent = computed(() => {
  if (!props.cpuCorePercents.length) return 0
  return props.cpuCorePercents.reduce((a, b) => a + Number(b), 0) / props.cpuCorePercents.length
})

const maxPercent = computed(() => {
  if (!props.cpuCorePercents.length) return 0
  return Math.max(...props.cpuCorePercents.map(Number))
})

const coreColor = (p) => {
  if (p >= 90) return 'text-red-500'
  if (p >= 80) return 'text-amber-500'
  return 'text-blue-500'
}

const barBg = (p) => {
  if (p >= 90) return 'bg-red-500'
  if (p >= 80) return 'bg-amber-500'
  return 'bg-blue-500'
}

const ringStroke = (p) => {
  if (p >= 90) return 'stroke-red-500'
  if (p >= 80) return 'stroke-amber-500'
  return 'stroke-blue-500'
}
</script>
