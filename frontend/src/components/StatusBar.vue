<template>
  <footer class="status-bar">
    <div class="max-w-screen-2xl mx-auto px-3 sm:px-6 lg:px-8 flex items-center justify-between h-full gap-2">
      <!-- Left: status info -->
      <div class="flex items-center gap-2.5 text-[11px] min-w-0 overflow-hidden">
        <!-- Connection indicator -->
        <span class="inline-flex items-center gap-1.5 flex-shrink-0">
          <span
            class="h-1.5 w-1.5 rounded-full flex-shrink-0"
            :class="isConnected ? 'bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.6)]' : 'bg-red-400'"
          ></span>
          <span :class="isConnected ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
            {{ isConnected ? t('live_label') : t('offline_label') }}
          </span>
        </span>

        <span class="sbar-divider"></span>

        <!-- Network IO -->
        <span class="inline-flex items-center gap-1 flex-shrink-0 text-gray-500 dark:text-gray-400" :title="t('statusbar_net_io')">
          <!-- Network icon: two arrows up/down over a globe-like shape -->
          <svg viewBox="0 0 24 24" class="h-3 w-3 text-cyan-500 dark:text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6" />
            <line x1="2" y1="20" x2="2.01" y2="20" />
          </svg>
          <span class="text-emerald-600 dark:text-emerald-400">↑{{ fmtSpeed(metrics.net_upload_speed) }}</span>
          <span class="text-blue-600 dark:text-blue-400">↓{{ fmtSpeed(metrics.net_download_speed) }}</span>
        </span>

        <span class="sbar-divider"></span>

        <!-- Disk IO -->
        <span class="inline-flex items-center gap-1 flex-shrink-0 text-gray-500 dark:text-gray-400" :title="t('statusbar_disk_io')">
          <!-- Disk icon: hard drive with activity indicator -->
          <svg viewBox="0 0 24 24" class="h-3 w-3 text-orange-500 dark:text-orange-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
          <span class="text-amber-600 dark:text-amber-400">R{{ fmtSpeed(metrics.run_disk_read_speed) }}</span>
          <span class="text-purple-600 dark:text-purple-400">W{{ fmtSpeed(metrics.run_disk_write_speed) }}</span>
        </span>

        <span class="sbar-divider hidden sm:block"></span>

        <!-- Last updated -->
        <span class="text-gray-400 dark:text-gray-500 truncate hidden sm:inline" v-if="lastUpdated">
          {{ lastUpdated }}
        </span>
      </div>

      <!-- Right: actions -->
      <div class="flex items-center gap-1 flex-shrink-0">
        <button
          @click="onOpenSystemInfo"
          class="sbar-btn"
          :title="t('sysinfo_title')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
            <path d="M7 8h2" /><path d="M7 11h4" /><circle cx="16" cy="9.5" r="2" />
          </svg>
          <span class="hidden sm:inline">{{ t('sysinfo_title') }}</span>
        </button>

        <span class="sbar-divider"></span>

        <button
          v-if="isAdmin"
          @click="onOpenTerminal"
          class="sbar-btn"
          :title="t('terminal')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" />
          </svg>
          <span class="hidden sm:inline">{{ t('terminal') }}</span>
        </button>
        <button
          @click="refreshStatus"
          class="sbar-btn"
          :title="t('refresh')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 12a8 8 0 1 1-2.34-5.66" /><path d="M20 4v6h-6" />
          </svg>
          <span class="hidden sm:inline">{{ t('refresh') }}</span>
        </button>
      </div>
    </div>
  </footer>
</template>

<script setup>
const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  isConnected: { type: Boolean, default: false },
  lastUpdated: { type: String, default: '' },
  metrics: { type: Object, default: () => ({}) },
  onOpenSystemInfo: { type: Function, required: true },
  onOpenTerminal: { type: Function, required: true },
  refreshStatus: { type: Function, required: true },
  t: { type: Function, required: true },
})

function fmtSpeed(val) {
  const v = val || 0
  if (v >= 1024) return (v / 1024).toFixed(1) + ' GB/s'
  if (v >= 1) return v.toFixed(1) + ' MB/s'
  return (v * 1024).toFixed(0) + ' KB/s'
}
</script>

<style scoped>
.status-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 28px;
  z-index: 30;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-top: 1px solid rgba(56, 189, 248, 0.25);
  box-shadow: 0 -2px 12px rgba(15, 23, 42, 0.04);
}
:deep(.dark) .status-bar,
.dark .status-bar {
  background: rgba(15, 23, 42, 0.88);
  border-top-color: rgba(56, 189, 248, 0.15);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.2);
}

.sbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: rgba(107, 114, 128, 1);
  transition: all 0.12s;
}
.sbar-btn:hover {
  background: rgba(243, 244, 246, 1);
  color: rgba(55, 65, 81, 1);
}
:deep(.dark) .sbar-btn,
.dark .sbar-btn {
  color: rgba(156, 163, 175, 1);
}
:deep(.dark) .sbar-btn:hover,
.dark .sbar-btn:hover {
  background: rgba(31, 41, 55, 1);
  color: rgba(229, 231, 235, 1);
}

.sbar-divider {
  width: 1px;
  height: 12px;
  background: rgba(209, 213, 219, 0.6);
  flex-shrink: 0;
}
:deep(.dark) .sbar-divider,
.dark .sbar-divider {
  background: rgba(55, 65, 81, 0.6);
}
</style>
