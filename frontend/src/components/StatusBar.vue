<template>
  <footer class="status-bar">
    <div class="max-w-screen-2xl mx-auto px-3 sm:px-6 lg:px-8 flex items-center justify-between h-full gap-2">
      <!-- Left group: identity & connection -->
      <div class="flex items-center gap-2 text-[11px] flex-shrink-0">
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

        <!-- Current user -->
        <span v-if="currentUser?.username" class="inline-flex items-center gap-1 flex-shrink-0 text-gray-500 dark:text-gray-400">
          <svg viewBox="0 0 24 24" class="h-3 w-3 text-sky-500 dark:text-sky-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
          </svg>
          <span class="truncate max-w-[60px]">{{ currentUser.username }}</span>
        </span>

        <span class="sbar-divider hidden sm:block"></span>

        <!-- Host IP -->
        <span v-if="metrics.host_ip" class="hidden sm:inline-flex items-center gap-1 flex-shrink-0 text-gray-500 dark:text-gray-400 font-mono">
          <svg viewBox="0 0 24 24" class="h-3 w-3 text-violet-500 dark:text-violet-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" /><rect x="2" y="14" width="20" height="8" rx="2" />
            <line x1="6" y1="6" x2="6.01" y2="6" /><line x1="6" y1="18" x2="6.01" y2="18" />
          </svg>
          {{ metrics.host_ip }}
        </span>
      </div>

      <!-- Center group: resource metrics -->
      <div class="flex items-center gap-2 text-[11px] min-w-0 overflow-hidden">
        <!-- CPU hot cores (clickable) -->
        <span class="sbar-metric cursor-pointer hover:opacity-80 transition-opacity" :title="t('statusbar_cpu_hot')" @click="onOpenCpuCores && onOpenCpuCores()">
          <svg viewBox="0 0 24 24" class="h-3 w-3 flex-shrink-0" :class="cpuHotColor" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" />
            <rect x="9" y="9" width="6" height="6" />
            <line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" />
            <line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" />
            <line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="15" x2="23" y2="15" />
            <line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="15" x2="4" y2="15" />
          </svg>
          <span class="font-mono" :class="cpuHotColor">{{ cpuHotCount }}/{{ cpuTotalCores }}</span>
        </span>

        <span class="sbar-divider"></span>

        <!-- Memory usage -->
        <span class="sbar-metric" :title="t('statusbar_mem')">
          <svg viewBox="0 0 24 24" class="h-3 w-3 flex-shrink-0" :class="memColor" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="6" width="20" height="12" rx="1" />
            <path d="M6 10v4" /><path d="M10 10v4" /><path d="M14 10v4" /><path d="M18 10v4" />
          </svg>
          <span class="font-mono" :class="memColor">{{ fmtGB(metrics.memory_used) }}/{{ fmtGB(metrics.memory_total) }}G</span>
        </span>

        <span class="sbar-divider"></span>

        <!-- Disk usage (clickable) -->
        <span class="sbar-metric cursor-pointer hover:opacity-80 transition-opacity" :title="t('statusbar_disk')" @click="onOpenDiskDetails && onOpenDiskDetails()">
          <svg viewBox="0 0 24 24" class="h-3 w-3 flex-shrink-0" :class="diskColor" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12H2" /><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
            <line x1="6" y1="16" x2="6.01" y2="16" /><line x1="10" y1="16" x2="10.01" y2="16" />
          </svg>
          <span class="font-mono" :class="diskColor">{{ metrics.disk_used || 0 }}/{{ metrics.disk_total || 0 }}G</span>
        </span>

        <span class="sbar-divider hidden md:block"></span>

        <!-- Network IO -->
        <span class="sbar-metric hidden md:inline-flex" :title="t('statusbar_net_io')">
          <svg viewBox="0 0 24 24" class="h-3 w-3 text-cyan-500 dark:text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6" />
            <line x1="2" y1="20" x2="2.01" y2="20" />
          </svg>
          <span class="text-emerald-600 dark:text-emerald-400">↑{{ fmtSpeed(metrics.net_upload_speed) }}</span>
          <span class="text-blue-600 dark:text-blue-400">↓{{ fmtSpeed(metrics.net_download_speed) }}</span>
        </span>

        <span class="sbar-divider hidden md:block"></span>

        <!-- Disk IO -->
        <span class="sbar-metric hidden md:inline-flex" :title="t('statusbar_disk_io')">
          <svg viewBox="0 0 24 24" class="h-3 w-3 text-orange-500 dark:text-orange-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
          <span class="text-amber-600 dark:text-amber-400">R{{ fmtSpeed(metrics.run_disk_read_speed) }}</span>
          <span class="text-purple-600 dark:text-purple-400">W{{ fmtSpeed(metrics.run_disk_write_speed) }}</span>
        </span>
      </div>

      <!-- Right group: timestamp + actions -->
      <div class="flex items-center gap-1.5 flex-shrink-0 text-[11px]">
        <!-- Last updated -->
        <span class="text-gray-400 dark:text-gray-500 font-mono hidden lg:inline" v-if="lastUpdated">
          {{ fmtTime(lastUpdated) }}
        </span>

        <span class="sbar-divider hidden lg:block" v-if="lastUpdated"></span>

        <button
          @click="onOpenSystemInfo"
          class="sbar-btn"
          :title="t('sysinfo_title')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
            <path d="M7 8h2" /><path d="M7 11h4" /><circle cx="16" cy="9.5" r="2" />
          </svg>
        </button>
        <button
          v-if="isAdmin"
          @click="onOpenTerminal"
          class="sbar-btn"
          :title="t('terminal')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" />
          </svg>
        </button>
        <button
          @click="refreshStatus"
          class="sbar-btn"
          :title="t('refresh')"
        >
          <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 12a8 8 0 1 1-2.34-5.66" /><path d="M20 4v6h-6" />
          </svg>
        </button>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentUser: { type: [Object, null], default: null },
  isAdmin: { type: Boolean, default: false },
  isConnected: { type: Boolean, default: false },
  lastUpdated: { type: String, default: '' },
  metrics: { type: Object, default: () => ({}) },
  onOpenCpuCores: { type: Function, default: null },
  onOpenDiskDetails: { type: Function, default: null },
  onOpenSystemInfo: { type: Function, required: true },
  onOpenTerminal: { type: Function, required: true },
  refreshStatus: { type: Function, required: true },
  t: { type: Function, required: true },
})

const cpuTotalCores = computed(() => {
  const arr = props.metrics?.cpu_percents
  return Array.isArray(arr) ? arr.length : (props.metrics?.cpu_count || 0)
})

const cpuHotCount = computed(() => {
  const arr = props.metrics?.cpu_percents
  if (!Array.isArray(arr)) return 0
  return arr.filter(v => v >= 90).length
})

const cpuHotColor = computed(() => {
  const total = cpuTotalCores.value
  if (!total) return 'text-green-600 dark:text-green-400'
  const pct = (cpuHotCount.value / total) * 100
  if (pct >= 90) return 'text-red-500 dark:text-red-400'
  if (pct >= 50) return 'text-yellow-500 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
})

// memory_used / memory_total 单位 MB → GB
function fmtGB(mb) {
  const v = (mb || 0) / 1024
  return v >= 100 ? v.toFixed(0) : v.toFixed(1)
}

const memColor = computed(() => {
  const total = props.metrics?.memory_total || 1
  const pct = ((props.metrics?.memory_used || 0) / total) * 100
  if (pct >= 90) return 'text-red-500 dark:text-red-400'
  if (pct >= 70) return 'text-yellow-500 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
})

const diskColor = computed(() => {
  const total = props.metrics?.disk_total || 1
  const pct = ((props.metrics?.disk_used || 0) / total) * 100
  if (pct >= 90) return 'text-red-500 dark:text-red-400'
  if (pct >= 70) return 'text-yellow-500 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
})

function fmtSpeed(val) {
  const v = val || 0
  if (v >= 1024) return (v / 1024).toFixed(1) + ' GB/s'
  if (v >= 1) return v.toFixed(1) + ' MB/s'
  return (v * 1024).toFixed(0) + ' KB/s'
}

function fmtTime(iso) {
  try {
    const d = new Date(iso)
    if (isNaN(d)) return iso
    const Y = d.getFullYear()
    const M = String(d.getMonth() + 1).padStart(2, '0')
    const D = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    const ss = String(d.getSeconds()).padStart(2, '0')
    return `${Y}-${M}-${D} ${hh}:${mm}:${ss}`
  } catch { return iso }
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

.sbar-metric {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  color: rgba(107, 114, 128, 1);
}
:deep(.dark) .sbar-metric,
.dark .sbar-metric {
  color: rgba(156, 163, 175, 1);
}
</style>
