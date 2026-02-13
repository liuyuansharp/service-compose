<template>
  <footer class="status-bar">
    <div class="max-w-screen-2xl mx-auto px-3 sm:px-6 lg:px-8 flex items-center justify-between h-full gap-3">
      <!-- Left: status info -->
      <div class="flex items-center gap-3 text-[11px] min-w-0">
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

        <!-- Divider -->
        <span class="w-px h-3 bg-gray-300 dark:bg-gray-700 flex-shrink-0"></span>

        <!-- Last updated -->
        <span class="text-gray-500 dark:text-gray-400 truncate" v-if="lastUpdated">
          {{ t('last_updated') }}: {{ lastUpdated }}
        </span>
      </div>

      <!-- Right: actions -->
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <button
          @click="onOpenSystemInfo"
          class="sbar-btn"
          :title="t('sysinfo_title')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
            <path d="M7 8h2" /><path d="M7 11h4" /><circle cx="16" cy="9.5" r="2" />
          </svg>
          <span>{{ t('sysinfo_title') }}</span>
        </button>

        <span class="w-px h-3 bg-gray-300 dark:bg-gray-700"></span>

        <button
          v-if="isAdmin"
          @click="onOpenTerminal"
          class="sbar-btn"
          :title="t('terminal')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" />
          </svg>
          <span>{{ t('terminal') }}</span>
        </button>
        <button
          @click="refreshStatus"
          class="sbar-btn"
          :title="t('refresh')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 12a8 8 0 1 1-2.34-5.66" /><path d="M20 4v6h-6" />
          </svg>
          <span>{{ t('refresh') }}</span>
        </button>
      </div>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  isAdmin: { type: Boolean, default: false },
  isConnected: { type: Boolean, default: false },
  lastUpdated: { type: String, default: '' },
  onOpenSystemInfo: { type: Function, required: true },
  onOpenTerminal: { type: Function, required: true },
  refreshStatus: { type: Function, required: true },
  t: { type: Function, required: true },
})
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
</style>
