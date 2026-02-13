<template>
  <header class="tech-header border-b border-white/10">
    <div class="max-w-screen-2xl mx-auto px-3 sm:px-6 lg:px-8 py-3">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div class="flex-shrink-0">
          <h1 class="text-lg sm:text-2xl font-semibold text-gray-900 dark:text-slate-100 inline-flex items-center gap-2 sm:gap-3">
            {{ t('dashboard_title') }}
            <span class="tech-live-chip" :class="isConnected ? '' : 'tech-live-chip--offline'">
              <span class="tech-live-dot" :class="isConnected ? '' : 'tech-live-dot--offline'"></span>
              <span>{{ isConnected ? t('live_label') : t('offline_label') }}</span>
            </span>
          </h1>
          <p class="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mt-1">{{ t('dashboard_subtitle') }}</p>
        </div>
        <div class="w-full sm:w-auto sm:text-right">
          <div class="flex flex-wrap items-center justify-start sm:justify-end gap-2 sm:gap-3 text-sm text-gray-600">
            <span class="inline-flex items-center gap-2 text-gray-600 dark:text-gray-300">
              <span class="h-7 w-7 rounded-full border border-cyan-300/60 dark:border-cyan-400/30 bg-white/60 dark:bg-slate-800/60 shadow-[0_0_10px_rgba(34,211,238,0.35)] flex items-center justify-center flex-shrink-0">
                <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-600 dark:text-cyan-300" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="8" r="3.5" />
                  <path d="M4 20c1.8-3.6 5-5.4 8-5.4s6.2 1.8 8 5.4" />
                  <path d="M6 8h2M16 8h2" />
                </svg>
              </span>
              <span class="truncate max-w-[80px] sm:max-w-none">{{ currentUser?.username || t('user') }}</span>
              <span
                class="text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0"
                :class="
                  userRole === 'admin'
                    ? 'bg-red-500/20 text-red-400 border border-red-400/30'
                    : userRole === 'operator'
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-400/30'
                    : 'bg-gray-500/20 text-gray-400 border border-gray-400/30'
                "
              >{{ t('role_' + userRole) }}</span>
            </span>
            <button
              v-if="isAdmin"
              @click="onOpenUserManagement"
              class="px-2 sm:px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button inline-flex items-center gap-1"
              :title="t('user_management')"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="9" cy="7" r="3" />
                <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
                <path d="M19 8v6" />
                <path d="M16 11h6" />
              </svg>
              <span class="hidden sm:inline">{{ t('user_management') }}</span>
            </button>
            <button
              @click="onOpenAuditLog"
              class="px-2 sm:px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button inline-flex items-center gap-1"
              :title="t('audit_log')"
            >
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
              <span class="hidden sm:inline">{{ t('audit_log') }}</span>
            </button>
            <button
              @click="onLogout"
              class="px-2 sm:px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button"
            >
              {{ t('logout') }}
            </button>
            <button
              @click="toggleLanguage"
              class="px-2 sm:px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button"
            >
              {{ langLabel }}
            </button>
            <button
              @click="toggleTheme"
              class="px-2 sm:px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button"
            >
              {{ themeLabel }}
            </button>
          </div>
          <div class="mt-2 flex flex-wrap items-center justify-start sm:justify-end gap-2">
            <button
              v-if="isAdmin"
              @click="onOpenTerminal"
              class="px-3 py-1.5 bg-gray-700 text-white rounded-md hover:bg-gray-800 dark:bg-slate-600 dark:hover:bg-slate-500 transition text-sm inline-flex items-center gap-2 glass-button-solid"
              :title="t('terminal')"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="4 17 10 11 4 5" />
                <line x1="12" y1="19" x2="20" y2="19" />
              </svg>
              {{ t('terminal') }}
            </button>
            <button
              @click="refreshStatus"
              class="px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition text-sm inline-flex items-center gap-2 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 12a8 8 0 1 1-2.34-5.66" />
                <path d="M20 4v6h-6" />
              </svg>
              {{ t('refresh') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="tech-header-line"></div>
  </header>
</template>

<script setup>
defineProps({
  isAdmin: { type: Boolean, required: true },
  isConnected: { type: Boolean, default: false },
  currentUser: { type: [Object, null], default: null },
  userRole: { type: String, required: true },
  langLabel: { type: String, required: true },
  themeLabel: { type: String, required: true },
  onOpenUserManagement: { type: Function, required: true },
  onOpenAuditLog: { type: Function, required: true },
  onLogout: { type: Function, required: true },
  toggleLanguage: { type: Function, required: true },
  toggleTheme: { type: Function, required: true },
  onOpenTerminal: { type: Function, required: true },
  refreshStatus: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
