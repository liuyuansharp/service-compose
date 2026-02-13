<template>
  <!-- Service Info Modal -->
  <div
    v-if="serviceInfoVisible"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="closeServiceInfo"
  >
    <div class="tech-card rounded-md w-full max-w-3xl max-h-[90vh] sm:max-h-[85vh] flex flex-col">
      <div class="flex justify-between items-center p-4 sm:p-5 border-b border-gray-200 dark:border-slate-800">
        <div>
          <h3 class="text-lg sm:text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('info') }}</h3>
          <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ serviceInfo?.name || '—' }}</p>
        </div>
        <button
          @click="closeServiceInfo"
          class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
        >
          ✕
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-5 bg-gray-50 dark:bg-slate-950">
        <div v-if="serviceInfoLoading" class="text-sm text-gray-500 dark:text-slate-400">
          {{ t('loading_info') }}
        </div>
        <div v-else-if="serviceInfoError" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
          {{ serviceInfoError }}
        </div>
        <div v-else-if="!serviceInfo" class="text-sm text-gray-500 dark:text-slate-400">
          {{ t('no_info') }}
        </div>
        <div v-else class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="tech-card rounded-md p-4">
              <p class="text-xs text-gray-500 dark:text-slate-400">{{ t('info_name') }}</p>
              <p class="text-sm font-mono text-gray-800 dark:text-slate-100 mt-1">{{ serviceInfo.name }}</p>
            </div>
            <div class="tech-card rounded-md p-4">
              <div class="flex items-center justify-between">
                <p class="text-xs text-gray-500 dark:text-slate-400">{{ t('info_version') }}</p>
                <button
                  v-if="canOperate"
                  @click="onClickUpload"
                  class="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                >
                  {{ t('upload_package') }}
                </button>
              </div>
              <p class="text-sm font-mono text-gray-800 dark:text-slate-100 mt-1">{{ serviceInfo.version }}</p>
              <input
                v-if="canOperate"
                ref="updateFileInputRef"
                type="file"
                class="hidden"
                accept=".tar.gz"
                @change="handleUpdateFileChange"
              />
            </div>
            <div class="tech-card rounded-md p-4 md:col-span-2">
              <p class="text-xs text-gray-500 dark:text-slate-400">{{ t('info_commit') }}</p>
              <p class="text-sm font-mono text-gray-800 dark:text-slate-100 mt-1 break-all">{{ serviceInfo.commit_hash }}</p>
            </div>
          </div>
          <div class="tech-card rounded-md p-4">
            <p class="text-xs text-gray-500 dark:text-slate-400 mb-2">{{ t('info_build') }}</p>
            <pre class="text-xs font-mono text-gray-700 dark:text-slate-200 whitespace-pre-wrap">{{ serviceInfo.build_date }}</pre>
          </div>
          <div v-if="canOperate" class="tech-card rounded-md p-4">
            <div class="flex items-center justify-between mb-3">
              <p class="text-xs text-gray-500 dark:text-slate-400">{{ t('rollback_title') }}</p>
              <button
                @click="loadBackups(serviceInfo.name)"
                class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                {{ t('refresh') }}
              </button>
            </div>
            <div v-if="backupsLoading" class="text-xs text-gray-500 dark:text-slate-400">
              {{ t('rollback_loading') }}
            </div>
            <div v-else-if="backupsError" class="text-xs text-red-600">
              {{ backupsError }}
            </div>
            <div v-else-if="!backupOptions.length" class="text-xs text-gray-500 dark:text-slate-400">
              {{ t('rollback_empty') }}
            </div>
            <div v-else class="flex flex-col gap-3">
              <select
                v-model="selectedBackup"
                class="px-2 py-1 border border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded text-sm"
              >
                <option v-for="item in backupOptions" :key="item.name" :value="item.name">
                  {{ item.name }} ({{ item.created_at }})
                </option>
              </select>
              <button
                @click="rollbackToSelected"
                class="px-3 py-1.5 bg-amber-600 text-white rounded text-xs hover:bg-amber-700 transition"
              >
                {{ t('rollback_action') }}
              </button>
            </div>
          </div>
          <div v-if="canOperate && (uploadingUpdate || updatingService || updateProgress > 0)" class="tech-card rounded-md p-4">
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-slate-400">
              <span>{{ t('upload_progress') }}</span>
              <span class="font-mono">{{ uploadProgress }}%</span>
            </div>
            <div class="mt-2 h-2 rounded-full bg-gray-200 dark:bg-slate-800 overflow-hidden">
              <div class="h-full rounded-full bg-blue-500 transition-all" :style="{ width: `${uploadProgress}%` }"></div>
            </div>
            <div class="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-slate-400">
              <span>{{ t('update_progress') }}</span>
              <span class="font-mono">{{ updateProgress }}%</span>
            </div>
            <div class="mt-2 h-2 rounded-full bg-gray-200 dark:bg-slate-800 overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500 transition-all" :style="{ width: `${updateProgress}%` }"></div>
            </div>
            <div v-if="updateStatus" class="mt-3 text-xs font-medium text-gray-600 dark:text-slate-300">
              {{ updateStatus }}
            </div>
          </div>
          <!-- Scheduled Restart Section -->
          <div v-if="canOperate" class="tech-card rounded-md p-4">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <svg viewBox="0 0 24 24" class="h-4 w-4 text-amber-500" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                </svg>
                <p class="text-xs font-medium text-gray-700 dark:text-slate-300">{{ t('sched_title') }}</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :checked="schedForm.enabled"
                  @change="schedForm.enabled = $event.target.checked; if (!schedForm.enabled) saveScheduledRestart()"
                  class="sr-only peer"
                />
                <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:after:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
            <div v-if="schedForm.enabled" class="space-y-3">
              <div class="flex items-center gap-3">
                <label class="text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap">{{ t('sched_time') }}</label>
                <input
                  type="time"
                  v-model="schedForm.time"
                  class="flex-1 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-slate-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="text-xs text-gray-500 dark:text-slate-400 block mb-1.5">{{ t('sched_weekdays') }}</label>
                <div class="flex gap-1.5 flex-wrap">
                  <button
                    v-for="(dayLabel, dayIdx) in weekdayLabels"
                    :key="dayIdx"
                    @click="toggleWeekday(dayIdx)"
                    class="px-2 py-1 rounded text-[11px] font-medium transition"
                    :class="schedForm.weekdays.includes(dayIdx)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600'"
                  >{{ dayLabel }}</button>
                </div>
                <p class="text-[10px] text-gray-400 dark:text-gray-500 mt-1">{{ t('sched_weekdays_hint') }}</p>
              </div>
              <button
                @click="saveScheduledRestart"
                class="w-full px-3 py-1.5 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition font-medium"
              >{{ t('sched_save') }}</button>
              <div v-if="serviceInfo?.scheduled_restart?.next_restart || currentSchedNext" class="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                <svg viewBox="0 0 24 24" class="h-3.5 w-3.5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                {{ t('sched_next') }}: {{ formatAuditTime(currentSchedNext || serviceInfo?.scheduled_restart?.next_restart) }}
              </div>
              <div v-if="serviceInfo?.scheduled_restart?.last_restart" class="text-[11px] text-gray-400 dark:text-gray-500">
                {{ t('sched_last') }}: {{ formatAuditTime(serviceInfo.scheduled_restart.last_restart) }}
              </div>
            </div>
            <div v-else class="text-[11px] text-gray-400 dark:text-gray-500">{{ t('sched_disabled') }}</div>
          </div>
          <!-- Scheduled Restart Info (readonly) -->
          <div v-if="!canOperate && serviceInfo?.scheduled_restart" class="tech-card rounded-md p-4">
            <div class="flex items-center gap-2 mb-2">
              <svg viewBox="0 0 24 24" class="h-4 w-4 text-amber-500" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
              </svg>
              <p class="text-xs font-medium text-gray-700 dark:text-slate-300">{{ t('sched_title') }}</p>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="serviceInfo.scheduled_restart.enabled ? 'bg-green-500/15 text-green-600 dark:text-green-400' : 'bg-gray-500/15 text-gray-500'">
                {{ serviceInfo.scheduled_restart.enabled ? t('sched_enabled_label') : t('sched_disabled') }}
              </span>
            </div>
            <div v-if="serviceInfo.scheduled_restart.enabled" class="space-y-1 text-[11px] text-gray-500 dark:text-gray-400">
              <div>{{ t('sched_cron_label') }}: <span class="font-mono">{{ serviceInfo.scheduled_restart.cron }}</span></div>
              <div v-if="serviceInfo.scheduled_restart.next_restart">{{ t('sched_next') }}: {{ formatAuditTime(serviceInfo.scheduled_restart.next_restart) }}</div>
              <div v-if="serviceInfo.scheduled_restart.last_restart">{{ t('sched_last') }}: {{ formatAuditTime(serviceInfo.scheduled_restart.last_restart) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedBackup = defineModel('selectedBackup', { type: [String, null], default: null })

const updateFileInputRef = ref(null)
const onClickUpload = () => {
  updateFileInputRef.value?.click()
}

defineProps({
  serviceInfoVisible: { type: Boolean, required: true },
  serviceInfoLoading: { type: Boolean, required: true },
  serviceInfoError: { type: [String, null], default: null },
  serviceInfo: { type: [Object, null], default: null },
  canOperate: { type: Boolean, required: true },
  handleUpdateFileChange: { type: Function, required: true },
  loadBackups: { type: Function, required: true },
  backupsLoading: { type: Boolean, required: true },
  backupsError: { type: [String, null], default: null },
  backupOptions: { type: Array, required: true },
  rollbackToSelected: { type: Function, required: true },
  uploadingUpdate: { type: Boolean, required: true },
  updatingService: { type: Boolean, required: true },
  uploadProgress: { type: Number, required: true },
  updateProgress: { type: Number, required: true },
  updateStatus: { type: [String, null], default: null },
  schedForm: { type: Object, required: true },
  currentSchedNext: { type: [String, null], default: null },
  weekdayLabels: { type: Array, required: true },
  toggleWeekday: { type: Function, required: true },
  saveScheduledRestart: { type: Function, required: true },
  formatAuditTime: { type: Function, required: true },
  closeServiceInfo: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
