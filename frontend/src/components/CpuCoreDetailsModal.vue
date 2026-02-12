<template>
  <!-- CPU Core Details Modal -->
  <div
    v-if="cpuCoresVisible"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="closeCpuCores"
  >
    <div class="tech-card rounded-md w-full max-w-3xl max-h-[90vh] sm:max-h-[85vh] flex flex-col">
      <div class="flex justify-between items-center p-4 sm:p-5 border-b border-gray-200 dark:border-slate-800">
        <div>
          <h3 class="text-lg sm:text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('cpu_cores') }}</h3>
          <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ t('core_usage') }}</p>
        </div>
        <button
          @click="closeCpuCores"
          class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
        >
          ✕
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-5 bg-gray-50 dark:bg-slate-950">
        <div v-if="!cpuCorePercents.length" class="text-sm text-gray-500 dark:text-slate-400">
          {{ t('no_core_data') }}
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="(percent, idx) in cpuCorePercents"
            :key="idx"
            class="tech-card rounded-md p-3"
          >
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-slate-400">
              <span class="font-mono">{{ t('core') }} {{ idx + 1 }}</span>
              <span class="font-mono text-gray-700 dark:text-slate-200">{{ Number(percent).toFixed(0) }}%</span>
            </div>
            <div class="mt-2 h-2.5 rounded-full bg-gray-200 dark:bg-slate-800 overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="percent >= 90 ? 'bg-red-500' : percent >= 80 ? 'bg-amber-500' : 'bg-blue-500'"
                :style="{ width: `${Math.min(percent, 100)}%` }"
              ></div>
            </div>
            <div class="mt-2 text-xs font-semibold"
              :class="percent >= 90 ? 'text-red-500' : percent >= 80 ? 'text-amber-500' : 'text-blue-500'"
            >
              {{ percent >= 90 ? t('core_level_high') : percent >= 80 ? t('core_level_mid') : t('core_level_low') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  cpuCoresVisible: { type: Boolean, required: true },
  cpuCorePercents: { type: Array, required: true },
  closeCpuCores: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
