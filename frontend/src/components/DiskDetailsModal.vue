<template>
  <!-- Disk Details Modal -->
  <div
    v-if="diskDetailsVisible"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="closeDiskDetails"
  >
    <div class="tech-card rounded-md w-full max-w-5xl max-h-[90vh] sm:max-h-[85vh] flex flex-col">
      <div class="flex justify-between items-center p-4 sm:p-5 border-b border-gray-200 dark:border-slate-800">
        <div>
          <h3 class="text-lg sm:text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('disk_details') }}</h3>
          <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ t('disk_details_subtitle') }}</p>
        </div>
        <button
          @click="closeDiskDetails"
          class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
        >
          ✕
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-4 sm:p-5 bg-gray-50 dark:bg-slate-950">
        <div v-if="diskLoading" class="text-sm text-gray-500 dark:text-slate-400">
          {{ t('loading_disks') }}
        </div>
        <div v-else-if="diskError" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
          {{ diskError }}
        </div>
        <div v-else-if="!diskDetails.length" class="text-sm text-gray-500 dark:text-slate-400">
          {{ t('no_disk_data') }}
        </div>
        <div v-else class="space-y-3">
          <div class="hidden sm:grid grid-cols-12 text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wider">
            <div class="col-span-3">{{ t('disk_device') }}</div>
            <div class="col-span-3">{{ t('disk_mount') }}</div>
            <div class="col-span-2">{{ t('disk_type') }}</div>
            <div class="col-span-2 text-right">{{ t('disk_total') }}</div>
            <div class="col-span-2 text-right">{{ t('disk_usage') }}</div>
          </div>
          <div
            v-for="(disk, idx) in diskDetails"
            :key="`${disk.device}-${disk.mountpoint}-${idx}`"
            class="text-sm tech-card rounded-md p-3"
          >
            <!-- Desktop: grid layout -->
            <div class="hidden sm:grid grid-cols-12 items-center gap-3">
              <div class="col-span-3 font-mono text-gray-700 dark:text-slate-200 truncate" :title="disk.device">
                {{ disk.device || '—' }}
              </div>
              <div class="col-span-3 font-mono text-gray-600 dark:text-slate-300 truncate" :title="disk.mountpoint">
                {{ disk.mountpoint || '—' }}
              </div>
              <div class="col-span-2 text-gray-600 dark:text-slate-300">
                {{ disk.fstype || '—' }}
              </div>
              <div class="col-span-2 text-right font-mono text-gray-700 dark:text-slate-200">
                {{ disk.total_gb }} GB
              </div>
              <div class="col-span-2 text-right">
                <div class="text-xs font-mono text-gray-700 dark:text-slate-200">
                  {{ disk.used_gb }} / {{ disk.total_gb }} GB
                </div>
                <div class="mt-1 h-2 rounded-full bg-gray-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    class="h-full rounded-full"
                    :class="disk.percent >= 90 ? 'bg-red-500' : disk.percent >= 80 ? 'bg-amber-500' : 'bg-blue-500'"
                    :style="{ width: `${Math.min(disk.percent, 100)}%` }"
                  ></div>
                </div>
                <div class="mt-1 text-xs font-mono text-gray-500 dark:text-slate-400 text-right">
                  {{ Number(disk.percent).toFixed(0) }}%
                </div>
              </div>
            </div>
            <!-- Mobile: stacked layout -->
            <div class="sm:hidden space-y-2">
              <div class="flex items-center justify-between">
                <span class="font-mono text-xs text-gray-700 dark:text-slate-200 truncate flex-1" :title="disk.device">{{ disk.device || '—' }}</span>
                <span class="text-xs font-mono text-gray-500 dark:text-slate-400 ml-2">{{ disk.fstype || '—' }}</span>
              </div>
              <div class="text-xs font-mono text-gray-600 dark:text-slate-300 truncate" :title="disk.mountpoint">{{ disk.mountpoint || '—' }}</div>
              <div class="flex items-center justify-between text-xs font-mono text-gray-700 dark:text-slate-200">
                <span>{{ disk.used_gb }} / {{ disk.total_gb }} GB</span>
                <span class="font-semibold" :class="disk.percent >= 90 ? 'text-red-500' : disk.percent >= 80 ? 'text-amber-500' : 'text-blue-500'">{{ Number(disk.percent).toFixed(0) }}%</span>
              </div>
              <div class="h-2 rounded-full bg-gray-200 dark:bg-slate-800 overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="disk.percent >= 90 ? 'bg-red-500' : disk.percent >= 80 ? 'bg-amber-500' : 'bg-blue-500'"
                  :style="{ width: `${Math.min(disk.percent, 100)}%` }"
                ></div>
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
  diskDetailsVisible: { type: Boolean, required: true },
  diskDetails: { type: Array, required: true },
  diskLoading: { type: Boolean, required: true },
  diskError: { type: [String, null], default: null },
  closeDiskDetails: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
