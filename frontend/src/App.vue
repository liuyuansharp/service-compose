<template>
  <div :class="['min-h-screen', isDark ? 'dark bg-slate-950 text-slate-100' : 'bg-gray-50 text-gray-900']">
    <div v-if="!isAuthenticated" :class="['min-h-screen relative overflow-hidden flex items-center justify-center px-6 py-12', isDark ? 'login-shell-dark' : 'login-shell-light']">
      <div :class="isDark ? 'login-bg-dark' : 'login-bg-light'" class="absolute inset-0"></div>
      <div :class="isDark ? 'login-grid' : 'login-grid-light'" class="absolute inset-0"></div>
      <div :class="isDark ? 'login-scanlines' : 'login-scanlines-light'" class="absolute inset-0"></div>
      <div :class="isDark ? 'login-noise' : 'login-noise-light'" class="absolute inset-0"></div>
      <div class="absolute -top-24 -left-24 h-64 w-64 rounded-full blur-3xl login-orb login-orb-1"></div>
      <div class="absolute top-1/3 -right-32 h-72 w-72 rounded-full blur-3xl login-orb login-orb-2"></div>
      <div class="absolute bottom-0 left-1/4 h-52 w-52 rounded-full blur-3xl login-orb login-orb-3"></div>
  <div :class="['relative w-full max-w-4xl border backdrop-blur-xl rounded-2xl shadow-2xl login-panel', isDark ? 'border-white/10 bg-white/5 dark:bg-slate-900/40' : 'border-slate-200 bg-white/80']">
        <div class="grid md:grid-cols-2 gap-0">
          <div class="p-8 md:p-10 border-b md:border-b-0 md:border-r border-white/10">
            <div class="flex items-center justify-between">
              <div :class="['text-xs uppercase tracking-[0.25em]', isDark ? 'text-blue-200/70' : 'text-slate-500']">{{ t('login_tagline') }}</div>
              <div class="flex items-center gap-2">
                <button
                  @click="toggleTheme"
                  class="px-2.5 py-1 border border-white/20 rounded-full text-[11px] text-blue-100/80 hover:bg-white/10"
                >
                  {{ themeLabel }}
                </button>
                <button
                  @click="toggleLanguage"
                  class="px-2.5 py-1 border border-white/20 rounded-full text-[11px] text-blue-100/80 hover:bg-white/10"
                >
                  {{ langLabel }}
                </button>
              </div>
            </div>
            <h2 :class="['mt-6 text-2xl md:text-3xl font-semibold tracking-tight', isDark ? 'text-white' : 'text-slate-900']">
              {{ t('dashboard_title') }}
            </h2>
            <p :class="['mt-3 text-sm leading-relaxed', isDark ? 'text-blue-100/70' : 'text-slate-600']">
              {{ t('dashboard_subtitle') }}
            </p>
            <div :class="['mt-8 space-y-3 text-xs', isDark ? 'text-blue-100/60' : 'text-slate-600']">
              <div class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.8)]"></span>
                <span>{{ t('login_feature_realtime') }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.8)]"></span>
                <span>{{ t('login_feature_secure') }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]"></span>
                <span>{{ t('login_feature_overview') }}</span>
              </div>
            </div>
          </div>
          <div class="p-8 md:p-10">
            <div class="mb-6">
              <p :class="['text-xs uppercase tracking-[0.35em]', isDark ? 'text-blue-100/50' : 'text-slate-400']">{{ t('login') }}</p>
              <h3 :class="['mt-2 text-xl font-semibold', isDark ? 'text-white' : 'text-slate-900']">{{ t('welcome_back') }}</h3>
              <p :class="['mt-2 text-sm', isDark ? 'text-blue-100/70' : 'text-slate-500']">{{ t('login_required') }}</p>
            </div>
            <form class="space-y-4" @submit.prevent="handleLogin">
              <div>
                <label :class="['block text-xs font-medium mb-2', isDark ? 'text-blue-100/70' : 'text-slate-600']">{{ t('username') }}</label>
                <input
                  v-model="loginForm.username"
                  type="text"
                  autocomplete="username"
                  :class="['w-full px-3 py-2.5 rounded-lg focus:ring-2 focus:outline-none', isDark ? 'bg-white/5 border border-white/15 text-white placeholder:text-blue-100/40 focus:ring-cyan-400/70 focus:border-cyan-300/70' : 'bg-white border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:ring-blue-500/40 focus:border-blue-300']"
                  :placeholder="t('username_placeholder')"
                />
              </div>
              <div>
                <label :class="['block text-xs font-medium mb-2', isDark ? 'text-blue-100/70' : 'text-slate-600']">{{ t('password') }}</label>
                <input
                  v-model="loginForm.password"
                  type="password"
                  autocomplete="current-password"
                  :class="['w-full px-3 py-2.5 rounded-lg focus:ring-2 focus:outline-none', isDark ? 'bg-white/5 border border-white/15 text-white placeholder:text-blue-100/40 focus:ring-cyan-400/70 focus:border-cyan-300/70' : 'bg-white border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:ring-blue-500/40 focus:border-blue-300']"
                  :placeholder="t('password_placeholder')"
                />
              </div>
              <div v-if="loginError" class="text-sm text-red-200 bg-red-500/20 border border-red-400/40 rounded-lg px-3 py-2">
                {{ loginError }}
              </div>
              <button
                type="submit"
                :disabled="loginLoading"
                class="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-400 hover:to-blue-500 transition disabled:opacity-60 disabled:cursor-not-allowed shadow-[0_0_24px_rgba(56,189,248,0.35)]"
              >
                {{ loginLoading ? t('signing_in') : t('login') }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="relative min-h-screen overflow-hidden">
      <div :class="isDark ? 'auth-gradient-dark' : 'auth-gradient-light'" class="absolute inset-0"></div>
      <div :class="isDark ? 'auth-grid-dark' : 'auth-grid-light'" class="absolute inset-0"></div>
  <div :class="isDark ? 'auth-scanlines-dark' : 'auth-scanlines-light'" class="absolute inset-0"></div>
  <div :class="isDark ? 'auth-circuit-dark' : 'auth-circuit-light'" class="absolute inset-0"></div>
  <div class="absolute inset-0 auth-pulse"></div>
      <div :class="isDark ? 'auth-noise-dark' : 'auth-noise-light'" class="absolute inset-0"></div>
      <div
        v-if="statusAlerts.length"
        class="fixed top-4 right-4 z-50 w-[320px] max-w-[calc(100vw-2rem)] flex flex-col gap-3"
      >
        <div
          v-for="alert in statusAlerts"
          v-show="isStatusAlertVisible(alert.key)"
          :key="alert.key"
          role="button"
          tabindex="0"
          @click="focusAlertTarget(alert)"
          @keyup.enter="focusAlertTarget(alert)"
          :class="[
            'tech-card border rounded-md px-4 py-3 flex items-start gap-3 shadow-lg alert-pulse text-left w-full cursor-pointer',
            alert.level === 'critical'
              ? 'border-red-500/80 text-red-900 dark:text-red-100 alert-critical'
              : 'border-yellow-500/80 text-yellow-900 dark:text-yellow-100 alert-warning'
          ]"
        >
          <svg class="h-4 w-4 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 9v4"></path>
            <path d="M12 17h.01"></path>
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          </svg>
          <div class="text-sm flex-1">
            <div class="font-semibold">{{ alert.title }}</div>
            <div class="opacity-90">{{ alert.message }}</div>
          </div>
          <span
            class="text-xs opacity-70 hover:opacity-100 cursor-pointer"
            @click.stop="hideStatusAlert(alert.key)"
            :title="t('close')"
          >
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18"></path>
              <path d="M6 6l12 12"></path>
            </svg>
          </span>
        </div>
      </div>
      <div class="relative z-10">
    <!-- Header -->
    <header class="tech-header border-b border-white/10">
  <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900 dark:text-slate-100 inline-flex items-center gap-3">
              {{ t('dashboard_title') }}
              <span class="tech-live-chip">
                <span class="tech-live-dot"></span>
                <span>{{ t('live_label') }}</span>
              </span>
            </h1>
            <p class="text-sm text-gray-600 dark:text-slate-400 mt-1">{{ t('dashboard_subtitle') }}</p>
          </div>
          <div class="text-right">
            <div class="flex items-center justify-end gap-3 text-sm text-gray-600">
              <span class="inline-flex items-center gap-2 text-gray-600 dark:text-gray-300">
                <span class="h-7 w-7 rounded-full border border-cyan-300/60 dark:border-cyan-400/30 bg-white/60 dark:bg-slate-800/60 shadow-[0_0_10px_rgba(34,211,238,0.35)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-600 dark:text-cyan-300" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="8" r="3.5" />
                    <path d="M4 20c1.8-3.6 5-5.4 8-5.4s6.2 1.8 8 5.4" />
                    <path d="M6 8h2M16 8h2" />
                  </svg>
                </span>
                <span>{{ currentUser?.username || t('user') }}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded-full"
                  :class="userRole === 'admin' ? 'bg-red-500/20 text-red-400 border border-red-400/30' : userRole === 'operator' ? 'bg-blue-500/20 text-blue-400 border border-blue-400/30' : 'bg-gray-500/20 text-gray-400 border border-gray-400/30'"
                >{{ t('role_' + userRole) }}</span>
              </span>
              <!-- 用户管理（仅管理员） -->
              <button
                v-if="isAdmin"
                @click="showUserManagement = true; loadUsers()"
                class="px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button inline-flex items-center gap-1"
                :title="t('user_management')"
              >
                <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="9" cy="7" r="3" />
                  <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
                  <path d="M19 8v6" />
                  <path d="M16 11h6" />
                </svg>
                {{ t('user_management') }}
              </button>
              <button
                @click="logout()"
                class="px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button"
              >
                {{ t('logout') }}
              </button>
              <button
                @click="toggleLanguage"
                class="px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button"
              >
                {{ langLabel }}
              </button>
              <button
                @click="toggleTheme"
                class="px-3 py-1 border border-gray-200 dark:border-gray-700 rounded text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 glass-button"
              >
                {{ themeLabel }}
              </button>
            </div>
            <!-- <p class="text-xs text-gray-600 dark:text-slate-400 mt-2">{{ t('last_updated') }}: {{ formattedTimestamp }}</p> -->
            <div class="mt-2 flex items-center justify-end gap-2">
              <button
                v-if="isAdmin"
                @click="showTerminal = true"
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

    <!-- Main Content -->
  <main class="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="tech-shell">
        <div class="tech-ornament"></div>
      <div
        v-if="hasCriticalAlert"
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
      <!-- Status Overview Cards -->
  <div v-if="isCardVisible('overview')" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- Overall Status -->
  <div class="tech-card rounded-md p-4 border-l-4" :class="overallStatusBorder">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 dark:text-slate-400 text-xs font-medium">{{ t('overall_status') }}</p>
              <p class="text-2xl font-semibold mt-2 flex items-center gap-2" :class="statusColor">
                <span>{{ platformHealthLabel }}</span>
                <span
                  v-if="platformHealth === 'abnormal'"
                  class="inline-flex h-2 w-2 rounded-full bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.6)]"
                  :title="getHealthTooltip(platformStatus)"
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

        <!-- Active Services -->
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

        <!-- Last Updated -->
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

      <!-- System Metrics Cards -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- CPU Monitor -->
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
                <button
                  @click="openCpuCores"
                  class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {{ t('core_usage') }}
                </button>
              </div>
            </div>
      <div class="w-16 h-16 rounded-full border-4" 
        :class="[
          systemMetrics.cpu_percent < 50 ? 'border-green-500' : systemMetrics.cpu_percent < 80 ? 'border-yellow-500' : 'border-red-500',
          isCpuCritical ? 'ring-2 ring-red-400/70 ring-offset-2 ring-offset-white dark:ring-offset-slate-900' : ''
        ]"
                 style="display: flex; align-items: center; justify-content: center;">
              <svg class="w-12 h-12" :class="getCpuColor" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2"
                        :stroke-dasharray="251.2 * systemMetrics.cpu_percent / 100 + ' 251.2'"
                        transform="rotate(-90 50 50)" style="transition: all 0.3s ease;"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Memory Monitor -->
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
            </div>
      <div class="w-16 h-16 rounded-full border-4"
        :class="[
          systemMetrics.memory_percent < 50 ? 'border-green-500' : systemMetrics.memory_percent < 80 ? 'border-yellow-500' : 'border-red-500',
          isMemoryCritical ? 'ring-2 ring-red-400/70 ring-offset-2 ring-offset-white dark:ring-offset-slate-900' : ''
        ]"
                 style="display: flex; align-items: center; justify-content: center;">
              <svg class="w-12 h-12" :class="getMemoryColor" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2"
                        :stroke-dasharray="251.2 * systemMetrics.memory_percent / 100 + ' 251.2'"
                        transform="rotate(-90 50 50)" style="transition: all 0.3s ease;"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Disk Monitor -->
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
              <button
                @click="openDiskDetails"
                class="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                {{ t('disk_details') }}
              </button>
            </div>
      <div class="w-16 h-16 rounded-full border-4"
        :class="[
          systemMetrics.disk_percent < 50 ? 'border-green-500' : systemMetrics.disk_percent < 80 ? 'border-yellow-500' : 'border-red-500',
          isDiskCritical ? 'ring-2 ring-red-400/70 ring-offset-2 ring-offset-white dark:ring-offset-slate-900' : ''
        ]"
                 style="display: flex; align-items: center; justify-content: center;">
              <svg class="w-12 h-12" :class="getDiskColor" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2"
                        :stroke-dasharray="251.2 * systemMetrics.disk_percent / 100 + ' 251.2'"
                        transform="rotate(-90 50 50)" style="transition: all 0.3s ease;"/>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Platform Card -->
  <div
        v-if="isCardVisible('platform')"
        id="platform-card"
        class="tech-card rounded-md p-4 mb-6 border-t-4"
    :class="[platformCardBorderClass, getHealthBgClass(platformHealth), isFocusedTarget('platform') ? 'service-focus' : '']"
      >
        <div class="flex justify-between items-start mb-4">
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('platform') }}</h2>
            <p class="text-xs text-gray-600 dark:text-slate-400 mt-1">{{ t('platform_service') }}</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <button
              v-if="platformStatus.running && canOperate"
              @click="controlService('stop', 'platform')"
              class="px-3.5 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition text-sm inline-flex items-center gap-2.5 glass-button-solid"
              :disabled="controlling"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              {{ t('stop') }}
            </button>
            <button
              v-else-if="!platformStatus.running && canOperate"
              @click="controlService('start', 'platform')"
              class="px-3.5 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition text-sm inline-flex items-center gap-2.5 glass-button-solid"
              :disabled="controlling"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 6l10 6-10 6z" />
              </svg>
              {{ t('start') }}
            </button>
            <button
              @click="openServiceInfo('platform')"
              class="px-3.5 py-2 bg-slate-600 text-white rounded-md hover:bg-slate-700 transition text-sm inline-flex items-center gap-2.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 10v6" />
                <path d="M12 7h.01" />
              </svg>
              {{ t('info') }}
            </button>
            <button
              @click="openMetrics('platform')"
              class="px-3.5 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition text-sm inline-flex items-center gap-2.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 18V6" />
                <path d="M4 18h16" />
                <path d="M7 14l4-4 3 3 5-6" />
              </svg>
              {{ t('metrics') }}
            </button>
            <button
              @click="loadLogs('platform')"
              class="px-3.5 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition text-sm inline-flex items-center gap-2.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 4h7l4 4v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" />
                <path d="M9 12h6" />
                <path d="M9 16h6" />
              </svg>
              {{ t('logs') }}
            </button>
            <button
              v-if="platformLinkUrl"
              @click="openPlatformLink"
              class="px-3.5 py-2 bg-sky-600 text-white rounded-md hover:bg-sky-700 transition text-sm inline-flex items-center gap-2.5 glass-button-solid"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 14a4 4 0 0 1 0-6l2-2a4 4 0 0 1 6 6l-1.5 1.5" />
                <path d="M14 10a4 4 0 0 1 0 6l-2 2a4 4 0 0 1-6-6L7.5 10" />
              </svg>
              {{ t('platform_link') }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">{{ t('status') }}</p>
            <p class="text-base font-semibold mt-1 flex items-center gap-2" :class="platformHealthTextClass">
              <span>{{ platformHealthLabel }}</span>
              <span
                v-if="platformHealth === 'abnormal'"
                class="inline-flex h-2 w-2 rounded-full bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.6)]"
                :title="getHealthTooltip(platformStatus)"
              ></span>
            </p>
          </div>
          <div>
            <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">PID</p>
            <p class="text-base font-mono font-semibold mt-1">
              {{ platformStatus.pid || '—' }}
            </p>
            <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ t('uptime') }}: {{ platformUptimeDisplay }}</p>
          </div>
          <div class="md:col-span-2">
            <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">{{ t('last_log') }}</p>
            <p class="text-xs font-mono mt-1 text-gray-800 dark:text-slate-200 truncate">
              {{ platformStatus.last_log || t('no_logs_yet') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Services Grid -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('services') }}</h2>
          <div v-if="canOperate" class="flex items-center gap-2">
            <!-- 一键启动所有 -->
            <button
              @click="batchControlAll('start')"
              :disabled="controlling || allServicesRunning"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition
                     bg-emerald-600/90 text-white hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed
                     glass-button-solid shadow-sm"
              :title="t('batch_start_all')"
            >
              <!-- 播放/启动全部 icon -->
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="6 3 20 12 6 21 6 3" />
              </svg>
              <span>{{ t('batch_start_all') }}</span>
            </button>
            <!-- 一键停止所有 -->
            <button
              @click="batchControlAll('stop')"
              :disabled="controlling || noServicesRunning"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition
                     bg-red-600/90 text-white hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed
                     glass-button-solid shadow-sm"
              :title="t('batch_stop_all')"
            >
              <!-- 停止全部 icon -->
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="6" y="6" width="12" height="12" rx="1" />
              </svg>
              <span>{{ t('batch_stop_all') }}</span>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="service in visibleServices"
            :key="service.name"
            :id="serviceCardId(service.name)"
            draggable="true"
            @dragstart="onDragStart($event, service.name)"
            @dragend="onDragEnd"
            @dragover="onDragOver($event, service.name)"
            @dragleave="onDragLeave($event, service.name)"
            @drop="onDrop($event, service.name)"
            class="tech-card rounded-md p-4 transition service-draggable"
            :class="[
              getServiceBorderClass(service),
              getHealthBgClass(getHealthState(service)),
              isFocusedTarget(`service:${service.name}`) ? 'service-focus' : '',
              dragState.over === service.name && dragState.dragging !== service.name ? 'drag-over' : ''
            ]"
          >
            <div class="flex justify-between items-start mb-4">
              <div>
                <h3 class="text-base font-semibold text-gray-900 dark:text-slate-100">{{ service.name }}</h3>
                <p class="text-xs flex items-center gap-1" :class="getServiceHealthTextClass(service)">
                  <span>{{ getServiceHealthLabel(service) }}</span>
                  <span
                    v-if="getHealthState(service) === 'abnormal'"
                    class="inline-flex h-1.5 w-1.5 rounded-full bg-yellow-400 shadow-[0_0_6px_rgba(250,204,21,0.6)]"
                    :title="getHealthTooltip(service)"
                  ></span>
                </p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-if="service.running && canOperate"
                  @click="controlService('stop', service.name)"
                  class="px-2.5 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition inline-flex items-center gap-1.5 glass-button-solid"
                  :disabled="controlling"
                >
                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="6" y="6" width="12" height="12" rx="2" />
                  </svg>
                  {{ t('stop') }}
                </button>
                <button
                  v-else-if="!service.running && canOperate"
                  @click="controlService('start', service.name)"
                  class="px-2.5 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition inline-flex items-center gap-1.5 glass-button-solid"
                  :disabled="controlling"
                >
                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M8 6l10 6-10 6z" />
                  </svg>
                  {{ t('start') }}
                </button>
                <button
                  @click="openServiceInfo(service.name)"
                  class="px-2.5 py-1 bg-slate-600 text-white rounded text-xs hover:bg-slate-700 transition inline-flex items-center gap-1.5 glass-button-solid"
                >
                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 10v6" />
                    <path d="M12 7h.01" />
                  </svg>
                  {{ t('info') }}
                </button>
                <button
                  @click="openMetrics(service.name)"
                  class="px-2.5 py-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700 transition inline-flex items-center gap-1.5 glass-button-solid"
                >
                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 18V6" />
                    <path d="M4 18h16" />
                    <path d="M7 14l4-4 3 3 5-6" />
                  </svg>
                  {{ t('metrics') }}
                </button>
                <button
                  @click="loadLogs(service.name)"
                  class="px-2.5 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition inline-flex items-center gap-1.5 glass-button-solid"
                >
                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M7 4h7l4 4v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" />
                    <path d="M9 12h6" />
                    <path d="M9 16h6" />
                  </svg>
                  {{ t('logs') }}
                </button>
              </div>
            </div>

            <div class="space-y-3">
              <div>
                <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">PID</p>
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-xs font-mono dark:text-slate-200">{{ service.pid || '—' }}</p>
                    <p class="text-[11px] text-gray-500 dark:text-slate-400">{{ t('uptime') }}: {{ getServiceUptimeDisplay(service) }}</p>
                  </div>
              </div>
              <div>
                <p class="text-gray-600 dark:text-slate-400 text-xs uppercase tracking-wider">{{ t('last_log') }}</p>
                <p class="text-xs font-mono text-gray-700 dark:text-slate-300 truncate">
                  {{ service.last_log || t('no_logs_yet') }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </main>

    <!-- CPU Core Details Modal -->
    <div
      v-if="cpuCoresVisible"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="closeCpuCores"
    >
  <div class="tech-card rounded-md w-full max-w-3xl max-h-[85vh] flex flex-col">
        <div class="flex justify-between items-center p-5 border-b border-gray-200 dark:border-slate-800">
          <div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('cpu_cores') }}</h3>
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

    <!-- Disk Details Modal -->
    <div
      v-if="diskDetailsVisible"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="closeDiskDetails"
    >
  <div class="tech-card rounded-md w-full max-w-5xl max-h-[85vh] flex flex-col">
        <div class="flex justify-between items-center p-5 border-b border-gray-200 dark:border-slate-800">
          <div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('disk_details') }}</h3>
            <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ t('disk_details_subtitle') }}</p>
          </div>
          <button
            @click="closeDiskDetails"
            class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-5 bg-gray-50 dark:bg-slate-950">
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
            <div class="grid grid-cols-12 text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wider">
              <div class="col-span-3">{{ t('disk_device') }}</div>
              <div class="col-span-3">{{ t('disk_mount') }}</div>
              <div class="col-span-2">{{ t('disk_type') }}</div>
              <div class="col-span-2 text-right">{{ t('disk_total') }}</div>
              <div class="col-span-2 text-right">{{ t('disk_usage') }}</div>
            </div>
            <div
              v-for="(disk, idx) in diskDetails"
              :key="`${disk.device}-${disk.mountpoint}-${idx}`"
              class="grid grid-cols-12 items-center gap-3 text-sm tech-card rounded-md p-3"
            >
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
          </div>
        </div>
      </div>
    </div>

    <!-- Service Info Modal -->
    <div
      v-if="serviceInfoVisible"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="closeServiceInfo"
    >
  <div class="tech-card rounded-md w-full max-w-3xl max-h-[85vh] flex flex-col">
        <div class="flex justify-between items-center p-5 border-b border-gray-200 dark:border-slate-800">
          <div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">{{ t('info') }}</h3>
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
                    @click="triggerUpdateUpload"
                    class="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                  >
                    {{ t('upload_package') }}
                  </button>
                </div>
                <p class="text-sm font-mono text-gray-800 dark:text-slate-100 mt-1">{{ serviceInfo.version }}</p>
                <input
                  v-if="canOperate"
                  ref="updateFileInput"
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
          </div>
        </div>
      </div>
    </div>

    <!-- Rollback Confirm Modal -->
    <div
      v-if="rollbackConfirmVisible"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="cancelRollback"
    >
  <div class="tech-card rounded-md border border-red-200 dark:border-red-500/40 w-full max-w-md shadow-xl">
        <div class="p-5 border-b border-red-200 dark:border-red-500/40 bg-red-50 dark:bg-red-950/40">
          <div class="flex items-center gap-3">
            <span class="h-3 w-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.6)]"></span>
            <div>
              <h3 class="text-lg font-semibold text-red-700 dark:text-red-200">{{ t('rollback_confirm_title') }}</h3>
              <p class="text-xs text-red-600/80 dark:text-red-200/70">{{ t('rollback_confirm_message', { backup: rollbackPendingBackup || '—' }) }}</p>
            </div>
          </div>
        </div>
        <div class="p-5 text-sm text-gray-700 dark:text-slate-200">
          <div class="rounded-md border border-red-200/70 dark:border-red-500/30 bg-red-50/70 dark:bg-red-950/30 px-3 py-2">
            {{ t('rollback_confirm_message', { backup: rollbackPendingBackup || '—' }) }}
          </div>
          <p class="mt-3 text-xs text-red-600 dark:text-red-200/80">
            {{ t('rollback_confirm_warning') }}
          </p>
        </div>
        <div class="flex justify-end gap-3 px-5 pb-5">
          <button
            @click="cancelRollback"
            class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded text-gray-600 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {{ t('rollback_confirm_cancel') }}
          </button>
          <button
            @click="confirmRollback"
            class="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 shadow"
          >
            {{ t('rollback_confirm_ok') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Metrics Viewer Modal -->
    <div
      v-if="metricsService"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="closeMetrics"
    >
  <div class="tech-card rounded-md w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div class="flex flex-wrap justify-between items-center gap-3 p-5 border-b border-gray-200 dark:border-slate-800">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">
            {{ t('metrics') }} - {{ metricsService }} ({{ t('history') }})
          </h3>
          <div class="flex items-center gap-2">
            <select
              v-model.number="metricsRangeHours"
              class="px-2 py-1 border border-gray-300 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded text-sm"
            >
              <option :value="1">{{ t('range_1h') }}</option>
              <option :value="6">{{ t('range_6h') }}</option>
              <option :value="24">{{ t('range_24h') }}</option>
              <option :value="168">{{ t('range_7d') }}</option>
              <option :value="720">{{ t('range_30d') }}</option>
              <option :value="0">{{ t('range_all') }}</option>
            </select>
            <button
              @click="refreshMetricsHistory"
              class="px-3 py-1 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded text-sm hover:bg-gray-300 dark:hover:bg-gray-700"
            >
              {{ t('refresh') }}
            </button>
            <button
              @click="closeMetrics"
              class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
            >
              ✕
            </button>
          </div>
        </div>

  <div class="flex-1 overflow-y-auto p-5 bg-gray-50 dark:bg-slate-950">
          <div class="relative">
            <div
              v-if="metricsLoading"
              class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 text-gray-500 dark:text-slate-300 text-center p-8 rounded-md z-10"
            >
              {{ t('loading_metrics') }}
            </div>
            <div :class="['grid grid-cols-1 gap-6', metricsLoading ? 'opacity-50 pointer-events-none' : '']">
              <div class="tech-card rounded-md p-4">
                <div class="flex justify-between items-center mb-2">
                  <h4 class="font-semibold text-gray-800 dark:text-slate-100">CPU (%)</h4>
                  <span class="text-xs text-gray-500 dark:text-slate-400">
                    {{ t('latest') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.cpu_percent ?? 0 }}%
                  </span>
                </div>
                <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400 mb-2">
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-blue-600"></span>CPU
                  </span>
                </div>
                <div ref="cpuChartRef" class="w-full h-40"></div>
              </div>

              <div class="tech-card rounded-md p-4">
                <div class="flex justify-between items-center mb-2">
                  <h4 class="font-semibold text-gray-800 dark:text-slate-100">{{ t('memory') }} (MB)</h4>
                  <span class="text-xs text-gray-500 dark:text-slate-400">
                    {{ t('latest') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.memory_mb ?? 0 }} MB
                  </span>
                </div>
                <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400 mb-2">
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-purple-600"></span>{{ t('memory') }}
                  </span>
                </div>
                <div ref="memoryChartRef" class="w-full h-40"></div>
              </div>

              <div class="tech-card rounded-md p-4">
                <div class="flex justify-between items-center mb-2">
                  <h4 class="font-semibold text-gray-800 dark:text-slate-100">{{ t('disk_io') }} (MB/s)</h4>
                  <span class="text-xs text-gray-500 dark:text-slate-400">
                    {{ t('read') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.read_mb_s ?? 0 }} MB/s
                    · {{ t('write') }}: {{ getMetricsPoints(metricsService)?.slice(-1)[0]?.write_mb_s ?? 0 }} MB/s
                  </span>
                </div>
                <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-400 mb-2">
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-orange-500"></span>{{ t('read') }}
                  </span>
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-emerald-500"></span>{{ t('write') }}
                  </span>
                </div>
                <div ref="diskChartRef" class="w-full h-40"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Log Viewer Modal -->
    <div
      v-if="selectedService"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="selectedService = null"
    >
  <div class="tech-card rounded-md w-full max-w-4xl max-h-[90vh] flex flex-col">
        <!-- Modal Header -->
        <div class="flex justify-between items-center p-5 border-b border-gray-200 dark:border-slate-800">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">
            {{ t('logs') }} - {{ selectedService }}
          </h3>
          <button
            @click="selectedService = null"
            class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>

        <!-- Modal Controls -->
  <div class="flex flex-wrap gap-3 p-4 border-b border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-950">
           <button
             @click="() => { rememberCurrentPosition(); goToTop() }"
             class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition text-sm"
           >
             {{ t('top') }}
           </button>
           <button
             @click="() => { rememberCurrentPosition(); goToBottom() }"
             class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition text-sm"
           >
             {{ t('bottom') }}
           </button>
          <button
            @click="togglePause"
            class="px-4 py-2 rounded-md text-sm font-medium transition"
            :class="logPaused ? 'bg-green-600 text-white' : 'bg-blue-600 text-white'"
          >
            {{ logPaused ? t('resume') : t('pause') }}
          </button>

          <div class="flex-1 flex gap-2 items-center">
            <input
              v-model="logSearch"
              type="text"
              :placeholder="`${t('search_logs')}...`"
              class="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              @click="jumpToPrevMatch"
              class="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded text-xs hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              ‹ {{ t('prev') }}
            </button>
            <button
              @click="jumpToNextMatch"
              class="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded text-xs hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              {{ t('next') }} ›
            </button>
          </div>

          <button
            @click="downloadLogs"
            class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition text-sm"
          >
            {{ t('download') }}
          </button>

          <button
            @click="clearLogs"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition text-sm"
          >
            {{ t('clear') }}
          </button>
        </div>

        <!-- Modal Body - Logs Display -->
        <div
          ref="logsContainer"
          class="flex-1 overflow-y-auto p-4 bg-black font-mono text-sm"
          style="max-height: calc(90vh - 280px)"
        >
          <div v-if="logsLoading[selectedService]" class="text-gray-400 text-center py-8">
            {{ t('loading_logs') }}...
          </div>
          <div v-else-if="displayedLogs.length === 0" class="text-gray-500 text-center py-8">
            {{ t('no_logs_available') }}
          </div>
          <div
            v-for="(log, idx) in displayedLogs"
            :key="idx"
            class="mb-1 whitespace-pre-wrap break-words flex"
            :class="getLogColor(log.level)"
          >
            <span
              class="text-gray-500 mr-2 select-none w-16 text-right pr-2 border-r border-gray-700 cursor-pointer hover:text-white hover:bg-gray-800/60"
              :class="{
                'bg-yellow-700 text-white': logSearch &&
                  searchMatches[selectedService] &&
                  currentMatchIndex[selectedService] != null &&
                  currentMatchIndex[selectedService] >= 0 &&
                  // 使用原始行号对齐匹配：searchMatches 中存的是 0-based 行索引
                  searchMatches[selectedService][currentMatchIndex[selectedService]] === ((log.line || ((logsMeta[selectedService]?.offset || 0) + idx + 1)) - 1)
              }"
              @click="jumpToLogLine((log.line || ((logsMeta[selectedService]?.offset || 0) + idx + 1)) - 1)"
            >
              {{ log.line || ((logsMeta[selectedService]?.offset || 0) + idx + 1) }}
            </span>
            <span class="pl-2 flex-1">
              {{ log.raw }}
            </span>
          </div>
        </div>

        <!-- Modal Footer -->
  <div class="p-4 border-t border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-950 text-xs text-gray-600 dark:text-slate-300">
          {{ t('showing_logs', { count: displayedLogs.length }) }}
          <span v-if="logSearch">
            ({{ t('filtered_by') }}: "{{ logSearch }}")
            <span v-if="searchMatches[selectedService] && searchMatches[selectedService].length">
              &nbsp;|&nbsp;
              {{ t('match') }} {{ (currentMatchIndex[selectedService] ?? -1) + 1 }} / {{ searchMatches[selectedService].length }}
            </span>
          </span>
          <span v-if="selectedService && logsMeta[selectedService]">
            &nbsp;|&nbsp; {{ t('total_lines', { count: logsMeta[selectedService].total }) }}
          </span>
        </div>
      </div>
    </div>

    <!-- WebShell Terminal -->
    <!-- 最小化状态：底部浮动条 -->
    <div
      v-if="showTerminal && terminalMode === 'minimized'"
      class="fixed bottom-0 left-1/2 -translate-x-1/2 z-50 w-80 cursor-pointer select-none"
      @click="terminalMode = 'normal'"
    >
      <div class="bg-[#2d2d2d] border border-gray-600 border-b-0 rounded-t-lg px-4 py-2.5 flex items-center justify-between shadow-xl">
        <div class="flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="h-3.5 w-3.5 text-green-400" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="4 17 10 11 4 5" />
            <line x1="12" y1="19" x2="20" y2="19" />
          </svg>
          <span class="text-xs font-medium text-gray-200">{{ t('terminal_title') }}</span>
          <span
            class="h-1.5 w-1.5 rounded-full"
            :class="terminalConnected ? 'bg-green-400 shadow-[0_0_4px_rgba(74,222,128,0.6)]' : 'bg-red-400'"
          ></span>
        </div>
        <div class="flex items-center gap-1">
          <!-- 还原 -->
          <button @click.stop="terminalMode = 'normal'" class="text-gray-400 hover:text-white p-0.5" :title="t('terminal_restore')">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
            </svg>
          </button>
          <!-- 关闭 -->
          <button @click.stop="closeTerminal" class="text-gray-400 hover:text-red-400 p-0.5" :title="t('close')">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18" /><path d="M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 正常 / 最大化状态 -->
    <div
      v-show="showTerminal && terminalMode !== 'minimized'"
      class="fixed z-50"
      :class="terminalMode === 'maximized' ? 'inset-0' : 'inset-0 flex items-center justify-center p-4'"
      @click.self="terminalMode === 'normal' ? (terminalMode = 'minimized') : null"
    >
      <!-- 背景遮罩（仅 normal 模式） -->
      <div v-if="terminalMode === 'normal'" class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="terminalMode = 'minimized'"></div>

      <div
        class="relative flex flex-col bg-[#1e1e1e] border border-gray-700 shadow-2xl overflow-hidden"
        :class="terminalMode === 'maximized'
          ? 'w-full h-full'
          : 'rounded-lg w-full max-w-5xl h-[75vh]'"
      >
        <!-- Terminal Title Bar -->
        <div class="flex justify-between items-center px-3 py-1.5 bg-[#2d2d2d] border-b border-gray-700 select-none flex-shrink-0">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5 text-green-400" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="4 17 10 11 4 5" />
              <line x1="12" y1="19" x2="20" y2="19" />
            </svg>
            <span class="text-sm font-medium text-gray-200">{{ t('terminal_title') }}</span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded"
              :class="terminalConnected ? 'bg-green-600/30 text-green-300' : 'bg-red-600/30 text-red-300'"
            >
              {{ terminalConnected ? t('terminal_connected') : t('terminal_disconnected') }}
            </span>
          </div>
          <div class="flex items-center gap-0.5">
            <!-- 重连 -->
            <button
              v-if="!terminalConnected"
              @click="connectTerminal"
              class="px-2 py-0.5 text-[10px] bg-blue-600 text-white rounded hover:bg-blue-700 transition mr-1"
            >
              {{ t('terminal_reconnect') }}
            </button>
            <!-- 新窗口弹出 -->
            <button @click="popoutTerminal" class="term-win-btn" :title="t('terminal_popout')">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </button>
            <!-- 最小化 -->
            <button @click="terminalMode = 'minimized'" class="term-win-btn" :title="t('terminal_minimize')">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="18" x2="19" y2="18" />
              </svg>
            </button>
            <!-- 最大化 / 还原 -->
            <button @click="terminalMode = terminalMode === 'maximized' ? 'normal' : 'maximized'" class="term-win-btn" :title="terminalMode === 'maximized' ? t('terminal_restore') : t('terminal_maximize')">
              <svg v-if="terminalMode !== 'maximized'" viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
              </svg>
              <svg v-else viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="5" y="7" width="14" height="14" rx="2" />
                <path d="M9 7V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2" />
              </svg>
            </button>
            <!-- 关闭 -->
            <button @click="closeTerminal" class="term-win-btn hover:!bg-red-600 hover:!text-white" :title="t('close')">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 6L6 18" /><path d="M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <!-- Terminal Body -->
        <div ref="terminalContainer" class="flex-1 overflow-hidden"></div>
      </div>
    </div>

    <!-- User Management Modal -->
    <div
      v-if="showUserManagement"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="showUserManagement = false"
    >
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showUserManagement = false"></div>
      <div class="relative w-full max-w-4xl max-h-[85vh] flex flex-col bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div class="flex items-center gap-3">
            <div class="h-9 w-9 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center">
              <svg viewBox="0 0 24 24" class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="9" cy="7" r="3" />
                <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
                <path d="M19 8v6" />
                <path d="M16 11h6" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('user_management') }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('user_management_desc') }}</p>
            </div>
          </div>
          <button @click="showUserManagement = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-1">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
          </button>
        </div>
        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6">
          <!-- Add User Form -->
          <div class="mb-6 p-4 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-slate-800/50">
            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 8v6"/><path d="M16 11h6"/><circle cx="9" cy="7" r="3"/><path d="M3 21v-2a4 4 0 0 1 4-4h4"/></svg>
              {{ t('add_user') }}
            </h4>
            <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <input
                v-model="newUserForm.username"
                type="text"
                :placeholder="t('username')"
                class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
              <input
                v-model="newUserForm.password"
                type="password"
                :placeholder="t('password')"
                class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
              <select
                v-model="newUserForm.role"
                class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="admin">{{ t('role_admin') }}</option>
                <option value="operator">{{ t('role_operator') }}</option>
                <option value="readonly">{{ t('role_readonly') }}</option>
              </select>
              <button
                @click="createUser"
                :disabled="!newUserForm.username || !newUserForm.password"
                class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition inline-flex items-center justify-center gap-1.5"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
                {{ t('add') }}
              </button>
            </div>
          </div>

          <!-- User Table -->
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700">
                  <th class="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">{{ t('username') }}</th>
                  <th class="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">{{ t('role') }}</th>
                  <th class="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">{{ t('visible_cards_label') }}</th>
                  <th class="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">{{ t('created_at') }}</th>
                  <th class="text-right py-3 px-4 font-medium text-gray-600 dark:text-gray-400">{{ t('actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="u in userList"
                  :key="u.id"
                  class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition"
                >
                  <td class="py-3 px-4">
                    <div class="flex items-center gap-2">
                      <span class="h-7 w-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-semibold">
                        {{ u.username.charAt(0).toUpperCase() }}
                      </span>
                      <span class="font-medium text-gray-900 dark:text-white">{{ u.username }}</span>
                      <span v-if="u.username === currentUser?.username" class="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-700">{{ t('current_user_tag') }}</span>
                    </div>
                  </td>
                  <td class="py-3 px-4">
                    <select
                      v-if="editingUserId !== u.id"
                      :value="u.role"
                      @change="quickUpdateRole(u, $event.target.value)"
                      :disabled="u.username === currentUser?.username"
                      class="px-2 py-1 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-slate-800 text-xs text-gray-800 dark:text-gray-200 focus:outline-none"
                      :class="u.username === currentUser?.username ? 'opacity-50 cursor-not-allowed' : ''"
                    >
                      <option value="admin">{{ t('role_admin') }}</option>
                      <option value="operator">{{ t('role_operator') }}</option>
                      <option value="readonly">{{ t('role_readonly') }}</option>
                    </select>
                  </td>
                  <td class="py-3 px-4">
                    <button
                      @click="openVisibleCardsEditor(u)"
                      class="text-xs text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                    >
                      <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>
                      {{ u.visible_cards.length ? t('visible_cards_custom', { count: u.visible_cards.length }) : t('visible_cards_all') }}
                    </button>
                  </td>
                  <td class="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">{{ u.created_at ? u.created_at.slice(0, 10) : '—' }}</td>
                  <td class="py-3 px-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        @click="openResetPassword(u)"
                        class="text-xs text-amber-600 dark:text-amber-400 hover:underline"
                      >{{ t('reset_password') }}</button>
                      <button
                        v-if="u.username !== currentUser?.username"
                        @click="deleteUser(u)"
                        class="text-xs text-red-600 dark:text-red-400 hover:underline"
                      >{{ t('delete') }}</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Visible Cards Editor Sub-Modal -->
    <div
      v-if="showVisibleCardsEditor"
      class="fixed inset-0 z-[60] flex items-center justify-center p-4"
      @click.self="showVisibleCardsEditor = false"
    >
      <div class="absolute inset-0 bg-black/40" @click="showVisibleCardsEditor = false"></div>
      <div class="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h4 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('visible_cards_title', { user: editingVisibleUser?.username }) }}</h4>
          <button @click="showVisibleCardsEditor = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="p-6">
          <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{{ t('visible_cards_hint') }}</p>
          <div class="space-y-2.5">
            <label
              v-for="card in allCardOptions"
              :key="card.value"
              class="flex items-center gap-3 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer transition"
            >
              <input
                type="checkbox"
                :checked="editingVisibleCards.includes(card.value)"
                @change="toggleVisibleCard(card.value)"
                class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ card.label }}</span>
                <p class="text-[11px] text-gray-500 dark:text-gray-400">{{ card.desc }}</p>
              </div>
            </label>
          </div>
          <div class="mt-5 flex items-center justify-between">
            <button
              @click="editingVisibleCards = []"
              class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >{{ t('visible_cards_select_all') }}</button>
            <div class="flex gap-2">
              <button @click="showVisibleCardsEditor = false" class="px-4 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800">{{ t('cancel') }}</button>
              <button @click="saveVisibleCards" class="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">{{ t('save') }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reset Password Sub-Modal -->
    <div
      v-if="showResetPassword"
      class="fixed inset-0 z-[60] flex items-center justify-center p-4"
      @click.self="showResetPassword = false"
    >
      <div class="absolute inset-0 bg-black/40" @click="showResetPassword = false"></div>
      <div class="relative w-full max-w-sm bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h4 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('reset_password_title', { user: resetPasswordUser?.username }) }}</h4>
        </div>
        <div class="p-6 space-y-4">
          <input
            v-model="resetPasswordValue"
            type="password"
            :placeholder="t('new_password')"
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <div class="flex justify-end gap-2">
            <button @click="showResetPassword = false" class="px-4 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800">{{ t('cancel') }}</button>
            <button @click="doResetPassword" :disabled="!resetPasswordValue" class="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-40">{{ t('confirm') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <Teleport to="body">
      <div v-if="notification" class="fixed bottom-4 right-4 p-4 rounded-md border border-black/10 dark:border-white/10 text-white z-40 animate-slide-up"
        :class="notification.type === 'success' ? 'bg-green-600' : 'bg-red-600'"
      >
        {{ notification.message }}
        <div v-if="notification.details" class="mt-2 text-xs font-mono whitespace-pre-wrap bg-black/20 p-2 rounded max-h-40 overflow-auto">
          {{ notification.details }}
        </div>
      </div>
    </Teleport>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'
const logsContainer = ref(null)
const cpuChartRef = ref(null)
const memoryChartRef = ref(null)
const diskChartRef = ref(null)
const terminalContainer = ref(null)

// ---- WebShell Terminal ----
const showTerminal = ref(false)
const terminalConnected = ref(false)
const terminalMode = ref('normal') // 'normal' | 'minimized' | 'maximized'
let termInstance = null
let termFitAddon = null
let termWs = null
let termPopoutWindow = null

// ---- User Management ----
const showUserManagement = ref(false)
const userList = ref([])
const newUserForm = reactive({ username: '', password: '', role: 'readonly' })
const showVisibleCardsEditor = ref(false)
const editingVisibleUser = ref(null)
const editingVisibleCards = ref([])
const editingUserId = ref(null)
const showResetPassword = ref(false)
const resetPasswordUser = ref(null)
const resetPasswordValue = ref('')

const authToken = ref(localStorage.getItem('authToken') || '')
let storedUser = null
try {
  storedUser = localStorage.getItem('authUser')
} catch (e) {
  storedUser = null
}
const currentUser = ref(storedUser ? JSON.parse(storedUser) : null)
const loginForm = reactive({ username: '', password: '' })
const loginError = ref('')
const loginLoading = ref(false)
const isAuthenticated = computed(() => Boolean(authToken.value))
const userRole = computed(() => currentUser.value?.role || 'readonly')
const isAdmin = computed(() => userRole.value === 'admin')
const canOperate = computed(() => userRole.value === 'admin' || userRole.value === 'operator')
const lang = ref(localStorage.getItem('lang') || 'zh')
const isDark = ref(localStorage.getItem('theme') === 'dark')
const runtimeConfig = typeof window !== 'undefined' ? (window.APP_CONFIG || {}) : {}
const apiBaseUrl = (runtimeConfig.apiBaseUrl || '').replace(/\/+$/, '')
const wsBaseUrl = (runtimeConfig.wsBaseUrl || '').replace(/\/+$/, '')
const platformLinkUrl = (runtimeConfig.platformLinkUrl || '').trim()

const buildApiUrl = (path) => {
  if (!path) return path
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  if (!apiBaseUrl) return path
  return `${apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
}

const buildWsUrl = (path) => {
  if (!path) return path
  if (wsBaseUrl) {
    return `${wsBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
  }
  if (apiBaseUrl) {
    const wsFromApi = apiBaseUrl.replace(/^http/, 'ws')
    return `${wsFromApi}${path.startsWith('/') ? path : `/${path}`}`
  }
  const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const isDevOnVite = window.location.port === '5173'
  const wsHost = window.location.hostname
  const wsPort = isDevOnVite ? '8080' : (window.location.port || '8080')
  return `${wsProto}://${wsHost}:${wsPort}${path.startsWith('/') ? path : `/${path}`}`
}

const translations = {
  zh: {
    login: '登录',
    signing_in: '正在登录...',
    dashboard_title: '工作流服务管理仪表盘',
    dashboard_subtitle: '实时监控与控制',
  login_tagline: '系统接入',
  login_feature_realtime: '实时指标与状态',
  login_feature_secure: '安全控制通道',
  login_feature_overview: '多服务统一视图',
  live_label: '在线',
    username: '用户名',
    password: '密码',
    username_placeholder: '请输入用户名',
    password_placeholder: '请输入密码',
    logout: '退出登录',
    last_updated: '最后更新',
    refresh: '刷新',
    overall_status: '总体状态',
    running: '运行中',
  abnormal: '异常',
    stopped: '已停止',
  heartbeat_failed: '心跳失败',
  heartbeat_missing: '未配置心跳地址',
  heartbeat_timeout: '心跳超时',
  heartbeat_connection_error: '心跳连接失败',
  heartbeat_invalid_url: '心跳地址无效',
  heartbeat_http_error: '心跳返回 HTTP {code}',
  heartbeat_mock_failed: '心跳模拟失败',
    active_services: '运行服务',
    cpu_usage: 'CPU 使用率',
    memory_usage: '内存使用率',
    disk_usage: '磁盘使用率',
    disk_free: '可用',
    cores: '核',
    platform: '平台',
    platform_service: '平台服务',
  platform_link: '平台',
    start: '启动',
    stop: '停止',
    restart: '重启',
    metrics: '监控',
    logs: '日志',
    status: '状态',
    uptime: '运行时间',
    last_log: '最后日志',
    no_logs_yet: '暂无日志',
    services: '服务列表',
    history: '历史',
    range_1h: '近 1 小时',
    range_6h: '近 6 小时',
    range_24h: '近 24 小时',
    range_7d: '近 7 天',
    range_30d: '近 30 天',
    range_all: '全部历史',
    loading_metrics: '正在加载监控历史',
    latest: '最新',
    memory: '内存',
    disk_io: '磁盘 IO',
    read: '读取',
    write: '写入',
    top: '顶部',
    bottom: '底部',
    resume: '继续',
    pause: '暂停',
    search_logs: '搜索日志',
    prev: '上一条',
    next: '下一条',
    download: '下载',
    clear: '清空',
    loading_logs: '正在加载日志',
    no_logs_available: '暂无日志',
    showing_logs: '显示 {count} 条日志',
    filtered_by: '过滤条件',
    match: '匹配',
    total_lines: '总行数 {count}',
    user: '用户',
    login_required: '请输入用户名和密码',
    login_failed: '登录失败',
    welcome_back: '欢迎回来',
    logged_out: '已退出登录',
    session_expired: '会话已过期，请重新登录',
    refresh_failed: '刷新失败',
    logs_load_failed: '加载日志失败',
    metrics_load_failed: '加载监控历史失败',
    control_failed: '操作失败',
    service_action_success: '服务{action}成功',
    download_success: '下载成功',
    download_failed: '下载失败',
    search_failed: '搜索失败',
    jump_failed: '跳转失败',
    dark_mode: '暗色模式',
    light_mode: '亮色模式',
    alert_title: '告警',
    alert_stopped_title: '服务已停止',
    alert_abnormal_title: '服务异常',
    close: '关闭',
    alert_metrics: '资源使用率过高',
    info: '信息',
    loading_info: '正在加载信息...',
    no_info: '暂无信息',
    info_failed: '获取信息失败',
    info_name: '名称',
    info_version: '版本',
    info_commit: '提交哈希',
    info_build: '构建日期',
    upload_package: '上传更新包',
    uploading: '正在上传...',
    updating: '正在更新...',
    upload_progress: '上传进度',
    update_progress: '更新进度',
    update_complete: '更新完成',
    update_failed: '更新失败',
    update_file_invalid: '仅支持上传 .tar.gz 文件',
    rollback_title: '历史回滚',
    rollback_select: '选择回滚版本',
    rollback_action: '回滚',
    rollback_success: '回滚成功',
    rollback_failed: '回滚失败',
    rollback_loading: '正在加载历史版本...',
    rollback_empty: '暂无历史版本',
    rollback_confirm_title: '确认回滚',
    rollback_confirm_message: '确定回滚到 {backup} 吗？',
    rollback_confirm_warning: '该操作会替换当前版本并重启服务，请谨慎操作。',
    rollback_confirm_cancel: '取消',
    rollback_confirm_ok: '确认回滚',
    disk_details: '磁盘详情',
    disk_details_subtitle: '系统物理磁盘列表',
    disk_device: '设备',
    disk_mount: '挂载点',
    disk_type: '类型',
    disk_total: '总容量',
    loading_disks: '正在加载磁盘信息...',
    no_disk_data: '暂无磁盘数据',
    disk_details_failed: '获取磁盘信息失败',
    cpu_cores: 'CPU 核心',
    core_usage: '每核使用率',
    core_level: '等级',
    core_level_high: '高',
    core_level_mid: '中',
    core_level_low: '低',
    core: '核心',
    no_core_data: '暂无核心数据',
    terminal: '终端',
    terminal_title: '终端',
    terminal_connecting: '正在连接...',
    terminal_connected: '已连接',
    terminal_disconnected: '连接已断开',
    terminal_reconnect: '重连',
    terminal_minimize: '最小化',
    terminal_maximize: '最大化',
    terminal_restore: '还原',
    terminal_popout: '新窗口打开',
    batch_start_all: '全部启动',
    batch_stop_all: '全部停止',
    batch_start_confirm: '确定要启动所有服务吗？',
    batch_stop_confirm: '确定要停止所有服务吗？',
    batch_action_success: '批量{action}操作已执行',
    batch_action_failed: '批量{action}操作失败',
    role_admin: '管理员',
    role_operator: '操作员',
    role_readonly: '只读',
    role: '角色',
    user_management: '用户管理',
    user_management_desc: '管理用户角色和可见卡片权限',
    add_user: '新增用户',
    add: '添加',
    actions: '操作',
    created_at: '创建时间',
    visible_cards_label: '可见卡片',
    visible_cards_all: '全部可见',
    visible_cards_custom: '已选 {count} 项',
    visible_cards_title: '{user} - 可见卡片配置',
    visible_cards_hint: '不勾选任何项表示全部可见；勾选后仅显示选中的卡片。',
    visible_cards_select_all: '全部可见（清空选择）',
    card_overview: '总体状态',
    card_overview_desc: '运行状态、活跃服务数、系统指标',
    card_platform: '平台服务',
    card_platform_desc: '平台服务卡片及控制',
    card_service_desc: '{name} 服务卡片',
    current_user_tag: '当前',
    reset_password: '重置密码',
    reset_password_title: '{user} - 重置密码',
    new_password: '新密码',
    confirm: '确认',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    user_created: '用户创建成功',
    user_updated: '用户更新成功',
    user_deleted: '用户已删除',
    password_reset_success: '密码重置成功',
    delete_user_confirm: '确定要删除用户 {user} 吗？',
    permission_denied: '权限不足',
  },
  en: {
    login: 'Login',
    signing_in: 'Signing in...',
    dashboard_title: 'Workflow Service Manager Dashboard',
    dashboard_subtitle: 'Real-time monitoring and control',
  login_tagline: 'System Access',
  login_feature_realtime: 'Realtime metrics & status',
  login_feature_secure: 'Secure control access',
  login_feature_overview: 'Multi-service overview',
  live_label: 'Live',
    username: 'Username',
    password: 'Password',
    username_placeholder: 'Enter username',
    password_placeholder: 'Enter password',
    logout: 'Logout',
    last_updated: 'Last updated',
    refresh: 'Refresh',
    overall_status: 'Overall Status',
    running: 'Running',
  abnormal: 'Abnormal',
    stopped: 'Stopped',
  heartbeat_failed: 'Heartbeat failed',
  heartbeat_missing: 'Heartbeat URL missing',
  heartbeat_timeout: 'Heartbeat timeout',
  heartbeat_connection_error: 'Heartbeat connection error',
  heartbeat_invalid_url: 'Heartbeat URL invalid',
  heartbeat_http_error: 'Heartbeat returned HTTP {code}',
  heartbeat_mock_failed: 'Heartbeat mock failed',
    active_services: 'Active Services',
    cpu_usage: 'CPU Usage',
    memory_usage: 'Memory Usage',
    disk_usage: 'Disk Usage',
    disk_free: 'Free',
    cores: 'cores',
    platform: 'Platform',
    platform_service: 'Platform service',
  platform_link: 'Platform',
    start: 'Start',
    stop: 'Stop',
    restart: 'Restart',
    metrics: 'Metrics',
    logs: 'Logs',
    status: 'Status',
    uptime: 'Uptime',
    last_log: 'Last Log',
    no_logs_yet: 'No logs yet',
    services: 'Services',
    history: 'History',
    range_1h: 'Last 1h',
    range_6h: 'Last 6h',
    range_24h: 'Last 24h',
    range_7d: 'Last 7d',
    range_30d: 'Last 30d',
    range_all: 'All history',
    loading_metrics: 'Loading metrics history',
    latest: 'Latest',
    memory: 'Memory',
    disk_io: 'Disk IO',
    read: 'Read',
    write: 'Write',
    top: 'Top',
    bottom: 'Bottom',
    resume: 'Resume',
    pause: 'Pause',
    search_logs: 'Search logs',
    prev: 'Prev',
    next: 'Next',
    download: 'Download',
    clear: 'Clear',
    loading_logs: 'Loading logs',
    no_logs_available: 'No logs available',
    showing_logs: 'Showing {count} logs',
    filtered_by: 'filtered by',
    match: 'Match',
    total_lines: 'Total {count} lines',
    user: 'User',
    login_required: 'Username and password are required',
    login_failed: 'Login failed',
    welcome_back: 'Welcome back!',
    logged_out: 'Logged out successfully',
    session_expired: 'Session expired. Please log in again.',
    refresh_failed: 'Failed to refresh status',
    logs_load_failed: 'Failed to load logs',
    metrics_load_failed: 'Failed to load metrics history',
    control_failed: 'Service control failed',
    service_action_success: 'Service {action}ed successfully',
    download_success: 'Download completed',
    download_failed: 'Download failed',
    search_failed: 'Failed to search logs',
    jump_failed: 'Failed to jump',
    dark_mode: 'Dark mode',
    light_mode: 'Light mode',
    alert_title: 'Alert',
    alert_stopped_title: 'Service stopped',
    alert_abnormal_title: 'Service abnormal',
    close: 'Close',
    alert_metrics: 'High resource usage',
    info: 'Info',
    loading_info: 'Loading info...',
    no_info: 'No info',
    info_failed: 'Failed to load info',
    info_name: 'Name',
    info_version: 'Version',
    info_commit: 'Commit hash',
    info_build: 'Build date',
    upload_package: 'Upload package',
    uploading: 'Uploading...',
    updating: 'Updating...',
    upload_progress: 'Upload progress',
    update_progress: 'Update progress',
    update_complete: 'Update completed',
    update_failed: 'Update failed',
    update_file_invalid: 'Only .tar.gz files are supported',
    rollback_title: 'Rollback history',
    rollback_select: 'Select backup',
    rollback_action: 'Rollback',
    rollback_success: 'Rollback completed',
    rollback_failed: 'Rollback failed',
    rollback_loading: 'Loading backups...',
    rollback_empty: 'No backups available',
    rollback_confirm_title: 'Confirm rollback',
    rollback_confirm_message: 'Rollback to {backup}?',
    rollback_confirm_warning: 'This will replace the current version and restart the service.',
    rollback_confirm_cancel: 'Cancel',
    rollback_confirm_ok: 'Confirm rollback',
    disk_details: 'Disk details',
    disk_details_subtitle: 'Physical disks on this host',
    disk_device: 'Device',
    disk_mount: 'Mount',
    disk_type: 'Type',
    disk_total: 'Total',
    loading_disks: 'Loading disk info...',
    no_disk_data: 'No disk data',
    disk_details_failed: 'Failed to load disk info',
    cpu_cores: 'CPU Cores',
    core_usage: 'Per-core usage',
    core_level: 'Level',
    core_level_high: 'High',
    core_level_mid: 'Medium',
    core_level_low: 'Low',
    core: 'Core',
    no_core_data: 'No core data',
    terminal: 'Terminal',
    terminal_title: 'Terminal',
    terminal_connecting: 'Connecting...',
    terminal_connected: 'Connected',
    terminal_disconnected: 'Disconnected',
    terminal_reconnect: 'Reconnect',
    terminal_minimize: 'Minimize',
    terminal_maximize: 'Maximize',
    terminal_restore: 'Restore',
    terminal_popout: 'Pop out',
    batch_start_all: 'Start All',
    batch_stop_all: 'Stop All',
    batch_start_confirm: 'Are you sure you want to start all services?',
    batch_stop_confirm: 'Are you sure you want to stop all services?',
    batch_action_success: 'Batch {action} executed successfully',
    batch_action_failed: 'Batch {action} failed',
    role_admin: 'Admin',
    role_operator: 'Operator',
    role_readonly: 'Read-only',
    role: 'Role',
    user_management: 'Users',
    user_management_desc: 'Manage user roles and card visibility',
    add_user: 'Add User',
    add: 'Add',
    actions: 'Actions',
    created_at: 'Created',
    visible_cards_label: 'Visible Cards',
    visible_cards_all: 'All visible',
    visible_cards_custom: '{count} selected',
    visible_cards_title: '{user} - Visible Cards',
    visible_cards_hint: 'Leave all unchecked to show everything; check items to show only selected cards.',
    visible_cards_select_all: 'Show all (clear selection)',
    card_overview: 'Overview',
    card_overview_desc: 'Status, active services, system metrics',
    card_platform: 'Platform Service',
    card_platform_desc: 'Platform service card and controls',
    card_service_desc: '{name} service card',
    current_user_tag: 'You',
    reset_password: 'Reset Password',
    reset_password_title: '{user} - Reset Password',
    new_password: 'New password',
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    user_created: 'User created',
    user_updated: 'User updated',
    user_deleted: 'User deleted',
    password_reset_success: 'Password reset successfully',
    delete_user_confirm: 'Are you sure you want to delete user {user}?',
    permission_denied: 'Permission denied',
  }
}

const t = (key, vars = {}) => {
  let text = translations[lang.value]?.[key] || key
  Object.entries(vars).forEach(([k, v]) => {
    text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v)
  })
  return text
}

const openPlatformLink = () => {
  if (!platformLinkUrl) return
  window.open(platformLinkUrl, '_blank', 'noopener,noreferrer')
}

const updateDocumentMeta = () => {
  const title = t('dashboard_title')
  if (typeof document !== 'undefined') {
    document.title = title
    const langValue = lang.value === 'zh' ? 'zh-CN' : 'en'
    document.documentElement.lang = langValue
  }
}

watch(lang, () => {
  updateDocumentMeta()
}, { immediate: true })

const langLabel = computed(() => (lang.value === 'zh' ? 'EN' : '中文'))
const themeLabel = computed(() => (isDark.value ? t('light_mode') : t('dark_mode')))

const toggleLanguage = () => {
  lang.value = lang.value === 'zh' ? 'en' : 'zh'
}

const toggleTheme = () => {
  isDark.value = !isDark.value
}

// 实时仪表盘SSE
let dashboardEventSource = null
const setupDashboardSSE = () => {
  if (dashboardEventSource) dashboardEventSource.close()
  if (!authToken.value) return
  dashboardEventSource = new EventSource(buildApiUrl(`/api/dashboard/sse?token=${encodeURIComponent(authToken.value)}`))
  dashboardEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      platformStatus.value = data.platform
      mergeServicesData(data.services)
      systemMetrics.value = data.metrics
      lastUpdated.value = data.timestamp
      statusFetchedAt.value = Date.now()
      statusTicker.value = Date.now()
    } catch (e) {}
  }
  dashboardEventSource.onerror = () => {
    dashboardEventSource.close()
    dashboardEventSource = null
    // 降级为定时 fetch
    if (!dashboardEventSource && !statusInterval) {
      statusInterval = setInterval(refreshStatus, 5000)
    }
  }
}

// 日志WebSocket
let logSocket = null
let logSocketService = null
let logSocketReconnectTimer = null
const connectLogWebSocket = (service) => {
  if (!authToken.value) return
  logSocketService = service
  if (logSocketReconnectTimer) {
    clearTimeout(logSocketReconnectTimer)
    logSocketReconnectTimer = null
  }
  if (logSocket) logSocket.close()
  const token = authToken.value ? encodeURIComponent(authToken.value) : ''
  const wsUrl = buildWsUrl(`/api/ws/logs/${service}?token=${token}`)
  logSocket = new WebSocket(wsUrl)
  logSocket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'log') {
      logs.value[service] = [...(logs.value[service] || []), data]
      if (logsMeta.value[service]) logsMeta.value[service].total += 1
      nextTick(scrollLogsToBottom)
    }
  }
  logSocket.onclose = () => {
    // 只有在“日志窗口仍然打开且仍然是同一个 service”时才重连
    if (selectedService.value && logSocketService === selectedService.value && service === selectedService.value) {
      logSocketReconnectTimer = setTimeout(() => connectLogWebSocket(service), 2000)
    }
  }
}

const cleanupRealtime = () => {
  if (dashboardEventSource) {
    dashboardEventSource.close()
    dashboardEventSource = null
  }
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
  if (logSocketReconnectTimer) {
    clearTimeout(logSocketReconnectTimer)
    logSocketReconnectTimer = null
  }
  if (logSocket) {
    logSocket.close()
    logSocket = null
    logSocketService = null
  }
  if (metricsEventSource) {
    metricsEventSource.close()
    metricsEventSource = null
  }
  if (statusUptimeInterval) {
    clearInterval(statusUptimeInterval)
    statusUptimeInterval = null
  }
}

const logout = (silent = false) => {
  cleanupRealtime()
  closeMetrics()
  closeDiskDetails()
  closeServiceInfo()
  selectedService.value = null
  logs.value = {}
  logsMeta.value = {}
  logOffset.value = {}
  logHasMorePrev.value = {}
  logHasMoreNext.value = {}
  metricsHistory.value = {}
  diskDetails.value = []
  diskError.value = ''
  serviceInfo.value = null
  serviceInfoError.value = ''
  authToken.value = ''
  currentUser.value = null
  loginForm.password = ''
  if (!silent) {
    showNotification(t('logged_out'), 'success')
  }
}

const handleUnauthorized = () => {
  if (!authToken.value) return
  logout(true)
  showNotification(t('session_expired'), 'error')
}

const authorizedFetch = async (url, options = {}) => {
  if (!authToken.value) throw new Error('Not authenticated')
  const headers = new Headers(options.headers || {})
  if (!headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${authToken.value}`)
  }
  const response = await fetch(buildApiUrl(url), { ...options, headers })
  if (response.status === 401) {
    handleUnauthorized()
    throw new Error('Unauthorized')
  }
  if (response.status === 403) {
    showNotification(t('permission_denied'), 'error')
    throw new Error('Permission denied')
  }
  return response
}

const handleLogin = async () => {
  loginError.value = ''
  if (!loginForm.username || !loginForm.password) {
    loginError.value = t('login_required')
    return
  }
  loginLoading.value = true
  try {
    const response = await fetch(buildApiUrl('/api/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginForm)
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      const message = data?.detail || t('login_failed')
      throw new Error(message)
    }
    authToken.value = data.token
    currentUser.value = data.user
    loginForm.password = ''
    showNotification(t('welcome_back'), 'success')
  } catch (error) {
    loginError.value = error.message || t('login_failed')
  } finally {
    loginLoading.value = false
  }
}

const bootstrapSession = async () => {
  if (!authToken.value) return
  try {
    const response = await authorizedFetch('/api/me')
    const user = await response.json()
    currentUser.value = user
    await refreshStatus()
    setupDashboardSSE()
    if (!statusUptimeInterval) {
      statusUptimeInterval = setInterval(() => {
        statusTicker.value = Date.now()
      }, 1000)
    }
  } catch (error) {
    if (error.message === 'Unauthorized') return
    console.error('Bootstrap session error:', error)
  }
}

// State
const platformStatus = ref({
  name: 'platform',
  running: false,
  health: 'stopped',
  pid: null,
  last_log: null
})

const servicesStatus = ref([])

// ---- 服务卡片拖拽排序 ----
const dragState = reactive({
  dragging: null,    // 被拖拽的 service name
  over: null,        // 当前悬停的 service name
})
let _orderSavePending = false  // 拖拽保存还未完成时，SSE 更新保持本地顺序

/**
 * 用服务器最新数据更新 servicesStatus，但保持本地已有顺序
 * （当拖拽保存还在飞行中时，避免 SSE 覆盖回旧顺序）
 */
function mergeServicesData(incoming) {
  if (!servicesStatus.value.length || !_orderSavePending) {
    // 没有待保存的排序操作，直接使用服务器顺序
    servicesStatus.value = incoming
    return
  }
  // 有待保存操作，保留本地顺序，仅更新每个服务的数据
  const map = new Map(incoming.map(s => [s.name, s]))
  const merged = []
  for (const local of servicesStatus.value) {
    if (map.has(local.name)) {
      merged.push(map.get(local.name))
      map.delete(local.name)
    }
  }
  // 追加新增服务
  for (const s of map.values()) merged.push(s)
  servicesStatus.value = merged
}

let _saveOrderTimer = null
function saveServiceOrder(order) {
  _orderSavePending = true
  // 防抖：避免快速连续拖拽时频繁请求
  clearTimeout(_saveOrderTimer)
  _saveOrderTimer = setTimeout(async () => {
    try {
      await authorizedFetch('/api/preferences/service-order', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order })
      })
    } catch (e) {
      console.warn('Failed to save service order:', e)
    } finally {
      _orderSavePending = false
    }
  }, 300)
}

function onDragStart(e, serviceName) {
  dragState.dragging = serviceName
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', serviceName)
  requestAnimationFrame(() => {
    const el = document.getElementById(serviceCardId(serviceName))
    if (el) el.classList.add('drag-ghost')
  })
}
function onDragEnd() {
  if (dragState.dragging) {
    const el = document.getElementById(serviceCardId(dragState.dragging))
    if (el) el.classList.remove('drag-ghost')
  }
  dragState.dragging = null
  dragState.over = null
}
function onDragOver(e, serviceName) {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  if (dragState.over !== serviceName) {
    dragState.over = serviceName
  }
}
function onDragLeave(e, serviceName) {
  const card = document.getElementById(serviceCardId(serviceName))
  if (card && !card.contains(e.relatedTarget)) {
    if (dragState.over === serviceName) dragState.over = null
  }
}
function onDrop(e, targetName) {
  e.preventDefault()
  const srcName = dragState.dragging
  if (!srcName || srcName === targetName) {
    onDragEnd()
    return
  }
  // 在当前 servicesStatus 中交换位置
  const list = servicesStatus.value.map(s => s.name)
  const srcIdx = list.indexOf(srcName)
  const tgtIdx = list.indexOf(targetName)
  if (srcIdx < 0 || tgtIdx < 0) { onDragEnd(); return }
  // 直接重排 servicesStatus，即时生效
  const arr = [...servicesStatus.value]
  const [removed] = arr.splice(srcIdx, 1)
  arr.splice(tgtIdx, 0, removed)
  servicesStatus.value = arr
  // 持久化到后端配置文件
  saveServiceOrder(arr.map(s => s.name))
  onDragEnd()
}

// ---- WebShell Terminal functions ----
function connectTerminal() {
  if (termWs) {
    try { termWs.close() } catch (_) {}
    termWs = null
  }
  const wsUrl = buildWsUrl(`/api/ws/terminal?token=${encodeURIComponent(authToken.value)}`)
  termWs = new WebSocket(wsUrl)
  termWs.onopen = () => {
    terminalConnected.value = true
    if (termFitAddon && termInstance) {
      termFitAddon.fit()
      const dims = { type: 'resize', cols: termInstance.cols, rows: termInstance.rows }
      termWs.send(JSON.stringify(dims))
    }
  }
  termWs.onmessage = (e) => {
    if (termInstance) termInstance.write(e.data)
  }
  termWs.onclose = () => {
    terminalConnected.value = false
  }
  termWs.onerror = () => {
    terminalConnected.value = false
  }
}

function initTerminal() {
  if (termInstance) return
  termInstance = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace",
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
      selectionBackground: '#264f78',
      black: '#1e1e1e',
      red: '#f44747',
      green: '#6a9955',
      yellow: '#d7ba7d',
      blue: '#569cd6',
      magenta: '#c586c0',
      cyan: '#4ec9b0',
      white: '#d4d4d4',
    },
    scrollback: 5000,
    allowProposedApi: true,
  })
  termFitAddon = new FitAddon()
  termInstance.loadAddon(termFitAddon)
  termInstance.loadAddon(new WebLinksAddon())
  termInstance.open(terminalContainer.value)
  termFitAddon.fit()

  termInstance.onData((data) => {
    if (termWs && termWs.readyState === WebSocket.OPEN) {
      termWs.send(data)
    }
  })

  const resizeObserver = new ResizeObserver(() => {
    if (termFitAddon && showTerminal.value && terminalMode.value !== 'minimized') {
      termFitAddon.fit()
      if (termWs && termWs.readyState === WebSocket.OPEN && termInstance) {
        termWs.send(JSON.stringify({ type: 'resize', cols: termInstance.cols, rows: termInstance.rows }))
      }
    }
  })
  resizeObserver.observe(terminalContainer.value)
  termInstance._resizeObserver = resizeObserver

  connectTerminal()
}

function refitTerminal() {
  if (termFitAddon && termInstance) {
    nextTick(() => {
      termFitAddon.fit()
      if (termWs && termWs.readyState === WebSocket.OPEN) {
        termWs.send(JSON.stringify({ type: 'resize', cols: termInstance.cols, rows: termInstance.rows }))
      }
      termInstance.focus()
    })
  }
}

function closeTerminal() {
  showTerminal.value = false
  terminalMode.value = 'normal'
  if (termWs) {
    try { termWs.close() } catch (_) {}
    termWs = null
  }
  if (termInstance) {
    if (termInstance._resizeObserver) {
      termInstance._resizeObserver.disconnect()
    }
    termInstance.dispose()
    termInstance = null
    termFitAddon = null
  }
  terminalConnected.value = false
  if (termPopoutWindow && !termPopoutWindow.closed) {
    termPopoutWindow.close()
  }
  termPopoutWindow = null
}

function popoutTerminal() {
  // 关闭内嵌终端的 WS 和实例
  if (termWs) { try { termWs.close() } catch (_) {} termWs = null }
  if (termInstance) {
    if (termInstance._resizeObserver) termInstance._resizeObserver.disconnect()
    termInstance.dispose()
    termInstance = null
    termFitAddon = null
  }
  terminalConnected.value = false
  showTerminal.value = false
  terminalMode.value = 'normal'

  const wsUrl = buildWsUrl(`/api/ws/terminal?token=${encodeURIComponent(authToken.value)}`)
  const w = 920, h = 620
  const left = (screen.width - w) / 2, top = (screen.height - h) / 2
  const popup = window.open('', '_blank',
    `width=${w},height=${h},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no,resizable=yes`)
  if (!popup) return
  termPopoutWindow = popup

  // 收集当前页面中 xterm 相关的 CSS 规则
  let xtermCss = ''
  try {
    for (const sheet of document.styleSheets) {
      try {
        for (const rule of sheet.cssRules) {
          const text = rule.cssText
          if (text.includes('xterm') || text.includes('.xterm')) {
            xtermCss += text + '\n'
          }
        }
      } catch (_) { /* cross-origin sheets */ }
    }
  } catch (_) {}

  popup.document.write(`<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>${t('terminal_title')}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;background:#1e1e1e}
#term{width:100%;height:100%}
${xtermCss}
</style>
</head><body><div id="term"></div></body></html>`)
  popup.document.close()

  // 从父窗口作用域在弹窗 DOM 中创建 xterm
  const setupPopupTerminal = () => {
    try {
      if (popup.closed) return
      const container = popup.document.getElementById('term')
      if (!container) { setTimeout(setupPopupTerminal, 100); return }

      const term = new Terminal({
        cursorBlink: true, fontSize: 14,
        fontFamily: "'JetBrains Mono','Fira Code','Cascadia Code',Menlo,Monaco,'Courier New',monospace",
        theme: { background:'#1e1e1e', foreground:'#d4d4d4', cursor:'#d4d4d4',
          selectionBackground:'#264f78', black:'#1e1e1e', red:'#f44747',
          green:'#6a9955', yellow:'#d7ba7d', blue:'#569cd6',
          magenta:'#c586c0', cyan:'#4ec9b0', white:'#d4d4d4' },
        scrollback: 5000,
      })
      const fit = new FitAddon()
      term.loadAddon(fit)
      term.open(container)
      fit.fit()

      const ws = new WebSocket(wsUrl)
      ws.onopen = () => {
        fit.fit()
        ws.send(JSON.stringify({ type:'resize', cols: term.cols, rows: term.rows }))
      }
      ws.onmessage = (e) => term.write(e.data)
      ws.onclose = () => { term.write('\r\n\x1b[31m[disconnected]\x1b[0m\r\n') }
      term.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) ws.send(data)
      })
      const ro = new popup.ResizeObserver(() => {
        fit.fit()
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type:'resize', cols: term.cols, rows: term.rows }))
        }
      })
      ro.observe(container)
      popup.addEventListener('beforeunload', () => {
        ro.disconnect(); ws.close(); term.dispose()
      })
      term.focus()
    } catch (e) {
      if (!popup.closed) setTimeout(setupPopupTerminal, 150)
    }
  }
  setTimeout(setupPopupTerminal, 200)
}

watch(showTerminal, (val) => {
  if (val && terminalMode.value !== 'minimized') {
    nextTick(() => initTerminal())
  }
})

watch(terminalMode, (mode, oldMode) => {
  if (oldMode === 'minimized' && mode !== 'minimized') {
    // 从最小化还原时 refit
    nextTick(() => refitTerminal())
  }
  if (mode === 'normal' || mode === 'maximized') {
    nextTick(() => refitTerminal())
  }
})

const systemMetrics = ref({
  cpu_percent: 0,
  cpu_count: 0,
  cpu_percents: [],
  memory_percent: 0,
  memory_used: 0,
  memory_total: 0,
  disk_percent: 0,
  disk_used: 0,
  disk_total: 0,
  disk_free: 0,
  timestamp: ''
})
const selectedService = ref(null)
const metricsService = ref(null)
const cpuCoresVisible = ref(false)
const diskDetailsVisible = ref(false)
const diskDetails = ref([])
const diskLoading = ref(false)
const diskError = ref('')
const serviceInfoVisible = ref(false)
const serviceInfoLoading = ref(false)
const serviceInfoError = ref('')
const serviceInfo = ref(null)
const updateFileInput = ref(null)
const uploadingUpdate = ref(false)
const updatingService = ref(false)
const uploadProgress = ref(0)
const updateProgress = ref(0)
const updateStatus = ref('')
let updateTaskId = null
let updatePoller = null
const backupsLoading = ref(false)
const backupsError = ref('')
const backupOptions = ref([])
const selectedBackup = ref('')
const rollbackConfirmVisible = ref(false)
const rollbackPendingBackup = ref('')
const statusFetchedAt = ref(0)
const statusTicker = ref(0)
let statusUptimeInterval = null
const logs = ref({}) // { service: [log, ...] }
const logsLoading = ref({}) // { service: true/false }
const logsMeta = ref({}) // { service: { total, offset, ... } }
const logOffset = ref({}) // { service: 当前起始行号 }
const logHasMorePrev = ref({}) // { service: 是否还有上一页 }
const logHasMoreNext = ref({}) // { service: 是否还有下一页 }
// 记住每个 service 的上次查看位置
const logLastPosition = ref({}) // { service: { offset, scrollTop } }
// 搜索匹配的行号索引及当前匹配位置
const searchMatches = ref({}) // { service: [globalIndex1, globalIndex2, ...] }
const currentMatchIndex = ref({}) // { service: 当前匹配在 searchMatches 数组中的下标 }
const logPaused = ref(false)
const logSearch = ref('')
const lastUpdated = ref('')
const controlling = ref(false)
const notification = ref(null)
const statusAlertVisibility = ref({})
const focusedAlertKey = ref('')
let focusAlertTimer = null
const metricsHistory = ref({}) // { service: [points...] }
const metricsLoading = ref(false)
const metricsRangeHours = ref(24)
let metricsEventSource = null
let cpuChart = null
let memoryChart = null
let diskChart = null
let metricsResizeHandler = null
let logsScrollCleanup = null
const statusAlertTimers = ref({})
let statusAlertRepeatTimer = null

let statusInterval = null
let logsInterval = null

// Computed properties
const getHealthState = (item) => {
  if (!item) return 'stopped'
  return item.health || (item.running ? 'running' : 'stopped')
}

const getHealthLabel = (health) => {
  if (health === 'running') return `🟢 ${t('running')}`
  if (health === 'abnormal') return `🟡 ${t('abnormal')}`
  return `🔴 ${t('stopped')}`
}

const getHealthTextClass = (health) => {
  if (health === 'running') return 'text-green-600'
  if (health === 'abnormal') return 'text-yellow-600'
  return 'text-red-600'
}

const getHealthBorderClass = (health) => {
  if (health === 'running') return 'border-l-4 border-green-500 ring-1 ring-green-300/60'
  if (health === 'abnormal') return 'border-l-4 border-yellow-500 ring-1 ring-yellow-300/60'
  return 'border-l-4 border-slate-300 ring-1 ring-slate-200/70'
}

const getHealthBgClass = (health) => {
  if (health === 'running') return 'bg-green-50/70 dark:bg-emerald-950/30'
  if (health === 'abnormal') return 'bg-yellow-50/70 dark:bg-yellow-900/25'
  return 'bg-slate-200/70 dark:bg-slate-800/60'
}

const getHealthTooltip = (item) => {
  const reason = item?.health_reason
  if (!reason && item?.health === 'abnormal') return t('heartbeat_failed')
  if (reason === 'missing') return t('heartbeat_missing')
  if (reason === 'timeout') return t('heartbeat_timeout')
  if (reason === 'connection_error') return t('heartbeat_connection_error')
  if (reason === 'invalid_url') return t('heartbeat_invalid_url')
  if (reason === 'mock_fail') return t('heartbeat_mock_failed')
  if (typeof reason === 'string' && reason.startsWith('http_status_')) {
    const code = reason.replace('http_status_', '') || 'unknown'
    return t('heartbeat_http_error', { code })
  }
  if (reason === 'heartbeat_failed') return t('heartbeat_failed')
  if (item?.health === 'abnormal') return t('abnormal')
  return ''
}

const platformHealth = computed(() => getHealthState(platformStatus.value))
const platformHealthLabel = computed(() => getHealthLabel(platformHealth.value))
const platformHealthTextClass = computed(() => getHealthTextClass(platformHealth.value))
const platformCardBorderClass = computed(() => {
  const health = platformHealth.value
  if (health === 'running') return 'border-green-500 ring-1 ring-green-300/60'
  if (health === 'abnormal') return 'border-yellow-500 ring-1 ring-yellow-300/60'
  return 'border-slate-300 ring-1 ring-slate-200/70'
})

const getServiceHealthLabel = (service) => getHealthLabel(getHealthState(service))
const getServiceHealthTextClass = (service) => getHealthTextClass(getHealthState(service))
const getServiceBorderClass = (service) => getHealthBorderClass(getHealthState(service))

const statusAlerts = computed(() => {
  const items = []
  const platformHealth = getHealthState(platformStatus.value)
  if (platformStatus.value?.health && platformHealth !== 'running' && isCardVisible('platform')) {
    items.push({
      key: 'platform',
      name: t('platform'),
      health: platformHealth
    })
  }
  servicesStatus.value.forEach((service) => {
    const health = getHealthState(service)
    if (health !== 'running' && isCardVisible('service:' + service.name)) {
      items.push({
        key: `service:${service.name}`,
        name: service.name,
        health
      })
    }
  })

  return items
    .map((item) => {
    const isStopped = item.health === 'stopped'
    return {
      ...item,
      level: isStopped ? 'critical' : 'warning',
      title: isStopped ? t('alert_stopped_title') : t('alert_abnormal_title'),
      message: `${item.name} (${isStopped ? t('stopped') : t('abnormal')})`
    }
  })
    .sort((a, b) => {
      if (a.level === b.level) return 0
      return a.level === 'critical' ? -1 : 1
    })
})

const serviceCardId = (name) => {
  return `service-card-${String(name).replace(/[^a-zA-Z0-9_-]/g, '-')}`
}

const focusAlertTarget = async (alert) => {
  if (!alert?.key) return
  focusedAlertKey.value = alert.key
  if (focusAlertTimer) clearTimeout(focusAlertTimer)
  focusAlertTimer = setTimeout(() => {
    focusedAlertKey.value = ''
  }, 4000)

  await nextTick()
  const targetId = alert.key === 'platform' ? 'platform-card' : serviceCardId(alert.name)
  const target = typeof document !== 'undefined' ? document.getElementById(targetId) : null
  if (target?.scrollIntoView) {
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

const isFocusedTarget = (key) => focusedAlertKey.value === key

const runningCount = computed(() => {
  return servicesStatus.value.filter(s => getHealthState(s) === 'running').length
})

const allServicesRunning = computed(() => {
  return servicesStatus.value.length > 0 && runningCount.value === servicesStatus.value.length
})

const noServicesRunning = computed(() => {
  return runningCount.value === 0
})

const batchControlAll = async (action) => {
  if (!confirm(t(action === 'start' ? 'batch_start_confirm' : 'batch_stop_confirm'))) return
  controlling.value = true
  try {
    const response = await authorizedFetch('/api/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    })
    if (!response.ok) throw new Error(`Failed to ${action} all services`)
    const data = await response.json()
    const details = formatControlDetails(data)
    showNotification(t('batch_action_success', { action: t(action) }), 'success', details)
    await refreshStatus()
    schedulePostControlRefresh()
  } catch (error) {
    console.error('Batch control error:', error)
    showNotification(t('batch_action_failed', { action: t(action) }), 'error')
  } finally {
    controlling.value = false
  }
}

// ---- Card Visibility ----
const isCardVisible = (cardKey) => {
  const vc = currentUser.value?.visible_cards
  if (!vc || vc.length === 0) return true // empty = all visible
  return vc.includes(cardKey)
}

const visibleServices = computed(() => {
  const vc = currentUser.value?.visible_cards
  if (!vc || vc.length === 0) return servicesStatus.value
  return servicesStatus.value.filter(s => vc.includes('service:' + s.name))
})

const allCardOptions = computed(() => {
  const opts = [
    { value: 'overview', label: t('card_overview'), desc: t('card_overview_desc') },
    { value: 'platform', label: t('card_platform'), desc: t('card_platform_desc') },
  ]
  for (const s of servicesStatus.value) {
    opts.push({ value: 'service:' + s.name, label: s.name, desc: t('card_service_desc', { name: s.name }) })
  }
  return opts
})

// ---- User Management Functions ----
const loadUsers = async () => {
  try {
    const response = await authorizedFetch('/api/users')
    if (response.ok) {
      userList.value = await response.json()
    }
  } catch (e) {
    console.error('Load users error:', e)
  }
}

const createUser = async () => {
  try {
    const response = await authorizedFetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newUserForm)
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed')
    }
    showNotification(t('user_created'), 'success')
    newUserForm.username = ''
    newUserForm.password = ''
    newUserForm.role = 'readonly'
    await loadUsers()
  } catch (e) {
    showNotification(e.message, 'error')
  }
}

const quickUpdateRole = async (user, newRole) => {
  try {
    const response = await authorizedFetch(`/api/users/${user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole })
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed')
    }
    showNotification(t('user_updated'), 'success')
    await loadUsers()
  } catch (e) {
    showNotification(e.message, 'error')
    await loadUsers() // revert UI
  }
}

const deleteUser = async (user) => {
  if (!confirm(t('delete_user_confirm', { user: user.username }))) return
  try {
    const response = await authorizedFetch(`/api/users/${user.id}`, { method: 'DELETE' })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed')
    }
    showNotification(t('user_deleted'), 'success')
    await loadUsers()
  } catch (e) {
    showNotification(e.message, 'error')
  }
}

const openVisibleCardsEditor = (user) => {
  editingVisibleUser.value = user
  editingVisibleCards.value = [...(user.visible_cards || [])]
  showVisibleCardsEditor.value = true
}

const toggleVisibleCard = (cardValue) => {
  const idx = editingVisibleCards.value.indexOf(cardValue)
  if (idx >= 0) {
    editingVisibleCards.value.splice(idx, 1)
  } else {
    editingVisibleCards.value.push(cardValue)
  }
}

const saveVisibleCards = async () => {
  if (!editingVisibleUser.value) return
  try {
    const response = await authorizedFetch(`/api/users/${editingVisibleUser.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible_cards: editingVisibleCards.value })
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed')
    }
    showNotification(t('user_updated'), 'success')
    showVisibleCardsEditor.value = false
    await loadUsers()
    // If editing self, update currentUser
    if (editingVisibleUser.value.username === currentUser.value?.username) {
      currentUser.value = { ...currentUser.value, visible_cards: [...editingVisibleCards.value] }
    }
  } catch (e) {
    showNotification(e.message, 'error')
  }
}

const openResetPassword = (user) => {
  resetPasswordUser.value = user
  resetPasswordValue.value = ''
  showResetPassword.value = true
}

const doResetPassword = async () => {
  if (!resetPasswordUser.value || !resetPasswordValue.value) return
  try {
    const response = await authorizedFetch(`/api/users/${resetPasswordUser.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: resetPasswordValue.value })
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed')
    }
    showNotification(t('password_reset_success'), 'success')
    showResetPassword.value = false
  } catch (e) {
    showNotification(e.message, 'error')
  }
}

const formattedTimestamp = computed(() => {
  if (!lastUpdated.value) return '—'
  const d = new Date(lastUpdated.value)
  const pad = (n) => String(n).padStart(2, '0')
  const yyyy = d.getFullYear()
  const mm = pad(d.getMonth() + 1)
  const dd = pad(d.getDate())
  const hh = pad(d.getHours())
  const mi = pad(d.getMinutes())
  const ss = pad(d.getSeconds())
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
})

const overallStatusBorder = computed(() => {
  const health = platformHealth.value
  if (health === 'running') return 'border-green-500'
  if (health === 'abnormal') return 'border-yellow-500'
  return 'border-red-500'
})

const statusColor = computed(() => {
  return platformHealthTextClass.value
})

const getCpuColor = computed(() => {
  const cpu = systemMetrics.value.cpu_percent
  if (cpu < 50) return 'text-green-600'
  if (cpu < 80) return 'text-yellow-600'
  return 'text-red-600'
})

const getMemoryColor = computed(() => {
  const mem = systemMetrics.value.memory_percent
  if (mem < 50) return 'text-green-600'
  if (mem < 80) return 'text-yellow-600'
  return 'text-red-600'
})

const getDiskColor = computed(() => {
  const disk = systemMetrics.value.disk_percent
  if (disk < 50) return 'text-green-600'
  if (disk < 80) return 'text-yellow-600'
  return 'text-red-600'
})

const isCpuCritical = computed(() => systemMetrics.value.cpu_percent >= 90)
const isMemoryCritical = computed(() => systemMetrics.value.memory_percent >= 90)
const isDiskCritical = computed(() => systemMetrics.value.disk_percent >= 90)
const cpuCorePercents = computed(() => systemMetrics.value.cpu_percents || [])
const criticalItems = computed(() => {
  if (!isCardVisible('overview')) return []
  const items = []
  if (isCpuCritical.value) items.push(t('cpu_usage'))
  if (isMemoryCritical.value) items.push(t('memory_usage'))
  if (isDiskCritical.value) items.push(t('disk_usage'))
  return items
})
const hasCriticalAlert = computed(() => criticalItems.value.length > 0)

const formatDuration = (totalSeconds) => {
  if (totalSeconds == null || Number.isNaN(totalSeconds)) return '—'
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (lang.value === 'zh') {
    return `${days}天${hours}小时${minutes}分钟${secs}秒`
  }
  return `${days}d ${hours}h ${minutes}m ${secs}s`
}


const platformUptimeDisplay = computed(() => {
  const base = platformStatus.value?.uptime_seconds
  if (base == null) return platformStatus.value?.uptime || '—'
  const elapsed = Math.floor((Date.now() - statusFetchedAt.value) / 1000)
  return formatDuration(base + Math.max(elapsed, 0))
})

const getServiceUptimeDisplay = (service) => {
  const base = service?.uptime_seconds
  if (base == null) return service?.uptime || '—'
  const elapsed = Math.floor((Date.now() - statusFetchedAt.value) / 1000)
  return formatDuration(base + Math.max(elapsed, 0))
}

const openCpuCores = async () => {
  cpuCoresVisible.value = true
}

const closeCpuCores = () => {
  cpuCoresVisible.value = false
}

const openDiskDetails = async () => {
  diskDetailsVisible.value = true
  diskLoading.value = true
  diskError.value = ''
  try {
    const response = await authorizedFetch('/api/disks')
    if (!response.ok) throw new Error('Failed to load disk info')
    const data = await response.json()
    diskDetails.value = Array.isArray(data) ? data : []
  } catch (error) {
    diskError.value = error.message || t('disk_details_failed')
    showNotification(t('disk_details_failed'), 'error')
  } finally {
    diskLoading.value = false
  }
}

const closeDiskDetails = () => {
  diskDetailsVisible.value = false
}

const loadServiceInfo = async (serviceName) => {
  serviceInfoLoading.value = true
  serviceInfoError.value = ''
  try {
    const response = await authorizedFetch(`/api/info?service=${encodeURIComponent(serviceName)}`)
    if (!response.ok) throw new Error('Failed to load info')
    const data = await response.json()
    serviceInfo.value = data
  } catch (error) {
    serviceInfoError.value = error.message || t('info_failed')
    showNotification(t('info_failed'), 'error')
  } finally {
    serviceInfoLoading.value = false
  }
}

const openServiceInfo = async (serviceName) => {
  serviceInfoVisible.value = true
  serviceInfo.value = null
  backupsError.value = ''
  backupsLoading.value = true
  backupOptions.value = []
  selectedBackup.value = ''
  await loadServiceInfo(serviceName)
  await loadBackups(serviceName)
}

const closeServiceInfo = () => {
  serviceInfoVisible.value = false
  if (updatePoller) {
    clearInterval(updatePoller)
    updatePoller = null
  }
  updateTaskId = null
  uploadingUpdate.value = false
  updatingService.value = false
  uploadProgress.value = 0
  updateProgress.value = 0
  updateStatus.value = ''
  backupOptions.value = []
  selectedBackup.value = ''
  backupsError.value = ''
  backupsLoading.value = false
  rollbackConfirmVisible.value = false
  rollbackPendingBackup.value = ''
}

const loadBackups = async (serviceName) => {
  backupsLoading.value = true
  backupsError.value = ''
  try {
    const response = await authorizedFetch(`/api/update/backups?service=${encodeURIComponent(serviceName)}`)
    if (!response.ok) throw new Error('Failed to load backups')
    const data = await response.json()
    backupOptions.value = Array.isArray(data) ? data : []
    selectedBackup.value = backupOptions.value[0]?.name || ''
  } catch (error) {
    backupsError.value = error.message || t('rollback_failed')
  } finally {
    backupsLoading.value = false
  }
}

const rollbackToSelected = () => {
  if (!serviceInfo.value || !selectedBackup.value) return
  rollbackPendingBackup.value = selectedBackup.value
  rollbackConfirmVisible.value = true
}

const confirmRollback = async () => {
  if (!serviceInfo.value || !rollbackPendingBackup.value) return
  rollbackConfirmVisible.value = false
  try {
    const serviceName = encodeURIComponent(serviceInfo.value.name)
    const backupName = encodeURIComponent(rollbackPendingBackup.value)
    const response = await authorizedFetch(`/api/update/rollback?service=${serviceName}&backup=${backupName}`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Rollback failed')
    showNotification(t('rollback_success'), 'success')
    await loadBackups(serviceInfo.value.name)
    await loadServiceInfo(serviceInfo.value.name)
  } catch (error) {
    showNotification(t('rollback_failed'), 'error')
  } finally {
    rollbackPendingBackup.value = ''
  }
}

const cancelRollback = () => {
  rollbackConfirmVisible.value = false
  rollbackPendingBackup.value = ''
}

const triggerUpdateUpload = () => {
  if (!serviceInfo.value) return
  updateFileInput.value?.click()
}

const handleUpdateFileChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.name.endsWith('.tar.gz')) {
    showNotification(t('update_file_invalid'), 'error')
    event.target.value = ''
    return
  }
  uploadUpdatePackage(file)
  event.target.value = ''
}

const uploadUpdatePackage = (file) => {
  if (!serviceInfo.value) return
  uploadingUpdate.value = true
  updatingService.value = false
  uploadProgress.value = 0
  updateProgress.value = 0
  updateStatus.value = t('uploading')
  updateTaskId = null
  if (updatePoller) {
    clearInterval(updatePoller)
    updatePoller = null
  }

  const formData = new FormData()
  formData.append('file', file)
  const xhr = new XMLHttpRequest()
  const target = encodeURIComponent(serviceInfo.value.name || 'platform')
  xhr.open('POST', buildApiUrl(`/api/update/upload?service=${target}`))
  if (authToken.value) {
    xhr.setRequestHeader('Authorization', `Bearer ${authToken.value}`)
  }
  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      uploadProgress.value = Math.round((event.loaded / event.total) * 100)
    }
  }
  xhr.onload = () => {
    uploadingUpdate.value = false
    if (xhr.status >= 200 && xhr.status < 300) {
      uploadProgress.value = 100
      try {
        const data = JSON.parse(xhr.responseText)
        updateTaskId = data.task_id
      } catch (e) {
        updateTaskId = null
      }
      if (updateTaskId) {
        updateStatus.value = t('updating')
        startUpdatePolling()
      } else {
        updateStatus.value = t('update_failed')
      }
    } else {
      updateStatus.value = t('update_failed')
      showNotification(t('update_failed'), 'error')
    }
  }
  xhr.onerror = () => {
    uploadingUpdate.value = false
    updateStatus.value = t('update_failed')
    showNotification(t('update_failed'), 'error')
  }
  xhr.send(formData)
}

const startUpdatePolling = () => {
  if (!updateTaskId) return
  updatingService.value = true
  updatePoller = setInterval(async () => {
    try {
      const response = await authorizedFetch(`/api/update/progress?task_id=${updateTaskId}`)
      if (!response.ok) throw new Error('Failed to load progress')
      const data = await response.json()
      updateProgress.value = data.update_progress ?? 0
      if (data.status === 'completed') {
        updateStatus.value = t('update_complete')
        updatingService.value = false
        clearInterval(updatePoller)
        updatePoller = null
      } else if (data.status === 'failed') {
        updateStatus.value = t('update_failed')
        updatingService.value = false
        clearInterval(updatePoller)
        updatePoller = null
      }
    } catch (error) {
      updateStatus.value = t('update_failed')
      updatingService.value = false
      if (updatePoller) {
        clearInterval(updatePoller)
        updatePoller = null
      }
    }
  }, 1000)
}

watch(authToken, (token) => {
  if (token) {
    localStorage.setItem('authToken', token)
    bootstrapSession()
  } else {
    localStorage.removeItem('authToken')
    cleanupRealtime()
  }
})

watch(currentUser, (user) => {
  if (user) {
    localStorage.setItem('authUser', JSON.stringify(user))
  } else {
    localStorage.removeItem('authUser')
  }
})

watch(lang, (value) => {
  localStorage.setItem('lang', value)
})

watch(isDark, (value) => {
  localStorage.setItem('theme', value ? 'dark' : 'light')
})

const parseMetricsTimestamp = (timestamp) => {
  if (!timestamp) return null
  let safe = timestamp
  const [base, fractional = ''] = safe.split('.')
  const ms = fractional.replace(/Z$/i, '').slice(0, 3).padEnd(3, '0')
  safe = `${base}.${ms}Z`
  const t = Date.parse(safe)
  return Number.isNaN(t) ? null : t
}

const formatMetricsTime = (timestamp) => {
  const t = parseMetricsTimestamp(timestamp)
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const initMetricsCharts = () => {
  if (cpuChartRef.value) {
    if (cpuChart) cpuChart.dispose()
    cpuChart = echarts.init(cpuChartRef.value)
  }
  if (memoryChartRef.value) {
    if (memoryChart) memoryChart.dispose()
    memoryChart = echarts.init(memoryChartRef.value)
  }
  if (diskChartRef.value) {
    if (diskChart) diskChart.dispose()
    diskChart = echarts.init(diskChartRef.value)
  }

  metricsResizeHandler = () => {
    cpuChart?.resize()
    memoryChart?.resize()
    diskChart?.resize()
  }
  window.addEventListener('resize', metricsResizeHandler)
}

const ensureMetricsCharts = () => {
  if (!cpuChart && cpuChartRef.value) {
    cpuChart = echarts.init(cpuChartRef.value)
  }
  if (!memoryChart && memoryChartRef.value) {
    memoryChart = echarts.init(memoryChartRef.value)
  }
  if (!diskChart && diskChartRef.value) {
    diskChart = echarts.init(diskChartRef.value)
  }
}

const updateMetricsCharts = () => {
  const service = metricsService.value
  if (!service) return
  ensureMetricsCharts()
  const points = getMetricsPoints(service)
  if (!points || !points.length) return

  const labels = points.map(p => formatMetricsTime(p.timestamp))
  const cpuData = points.map(p => Number(p.cpu_percent ?? 0))
  const memData = points.map(p => Number(p.memory_mb ?? 0))
  const readData = points.map(p => Number(p.read_mb_s ?? 0))
  const writeData = points.map(p => Number(p.write_mb_s ?? 0))

  cpuChart?.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: labels, boundaryGap: false },
    yAxis: { type: 'value', name: '%' },
    series: [{
      name: 'CPU',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: cpuData,
      lineStyle: { color: '#2563eb', width: 2 }
    }]
  })

  memoryChart?.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: labels, boundaryGap: false },
    yAxis: { type: 'value', name: 'MB' },
    series: [{
      name: 'Memory',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: memData,
      lineStyle: { color: '#7c3aed', width: 2 }
    }]
  })

  diskChart?.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['Read', 'Write'], top: 0 },
    grid: { left: 60, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: labels, boundaryGap: false },
    yAxis: { type: 'value', name: 'MB/s' },
    series: [
      {
        name: 'Read',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: readData,
        lineStyle: { color: '#f97316', width: 2 }
      },
      {
        name: 'Write',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: writeData,
        lineStyle: { color: '#10b981', width: 2 }
      }
    ]
  })
}

const getMetricsPoints = (service) => {
  const points = metricsHistory.value[service] || []
  if (!metricsRangeHours.value || metricsRangeHours.value >= 24) return points
  const cutoff = Date.now() - metricsRangeHours.value * 3600 * 1000
  return points.filter(p => {
    const t = parseMetricsTimestamp(p.timestamp)
    return t && t >= cutoff
  })
}

const refreshMetricsHistory = async () => {
  const service = metricsService.value
  if (!service) return
  metricsLoading.value = true
  try {
    const response = await authorizedFetch(`/api/metrics/history?service=${service}`)
    if (!response.ok) throw new Error('Failed to load metrics history')
    const data = await response.json()
    metricsHistory.value[service] = data.points || []
    await nextTick()
    updateMetricsCharts()
  } catch (e) {
    console.error('Load metrics history error:', e)
    showNotification(t('metrics_load_failed'), 'error')
  } finally {
    metricsLoading.value = false
  }
}

const setupMetricsSSE = (service) => {
  if (!authToken.value) return
  if (metricsEventSource) metricsEventSource.close()
  metricsEventSource = new EventSource(buildApiUrl(`/api/metrics/sse?service=${service}&token=${encodeURIComponent(authToken.value || '')}`))
  metricsEventSource.onmessage = (event) => {
    try {
      const point = JSON.parse(event.data)
      const history = metricsHistory.value[service] || []
      const last = history[history.length - 1]
      if (last && last.timestamp === point.timestamp) {
        history[history.length - 1] = point
      } else {
        history.push(point)
      }
      metricsHistory.value[service] = history
    } catch (e) {}
  }
}

const openMetrics = async (service) => {
  metricsService.value = service
  await nextTick()
  initMetricsCharts()
  await refreshMetricsHistory()
  setupMetricsSSE(service)
  updateMetricsCharts()
}

const closeMetrics = () => {
  metricsService.value = null
  if (metricsEventSource) {
    metricsEventSource.close()
    metricsEventSource = null
  }
  if (metricsResizeHandler) {
    window.removeEventListener('resize', metricsResizeHandler)
    metricsResizeHandler = null
  }
  if (cpuChart) {
    cpuChart.dispose()
    cpuChart = null
  }
  if (memoryChart) {
    memoryChart.dispose()
    memoryChart = null
  }
  if (diskChart) {
    diskChart.dispose()
    diskChart = null
  }
}

// 监听 selectedService 变化，用于管理 WebSocket 连接
watch(selectedService, (newService, oldService) => {
  if (newService) {
    // 如果打开了新的日志窗口，则连接
    connectLogWebSocket(newService)
  } else if (oldService) {
    // 如果关闭了日志窗口（从一个 service 变为 null）
    if (logSocketReconnectTimer) {
      clearTimeout(logSocketReconnectTimer)
      logSocketReconnectTimer = null
    }
    if (logSocket) {
      logSocket.close()
      logSocket = null
      logSocketService = null
      console.log(`WebSocket connection closed for ${oldService}`)
    }
  }
})

// 全局搜索所有日志内容
const displayedLogs = computed(() => {
  return logs.value[selectedService.value] || []
})

const totalLogs = computed(() => {
  return logs.value[selectedService.value]?.length || 0
})

// 监听搜索输入，触发全量搜索
watch(logSearch, async (keyword) => {
  const service = selectedService.value
  if (!service) return
  if (!logPaused.value) {
    logPaused.value = true
    if (logSocket && logSocket.readyState === 1) {
      logSocket.send(JSON.stringify({ action: 'pause' }))
    }
  }
  logsLoading.value[service] = true
  try {
    const params = new URLSearchParams({ service, lines: '200', offset: '0' })
    if (keyword) params.append('search', keyword)
    const response = await authorizedFetch(`/api/logs?${params.toString()}`)
    if (!response.ok) throw new Error('Failed to search logs')
    const data = await response.json()
    logs.value[service] = data.logs
    logsMeta.value[service] = { total: data.total, offset: data.offset, searched: data.searched }
    logOffset.value[service] = data.offset
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    // 记录当前批次中的匹配行号（使用全局行号 data.offset + index）
    if (keyword) {
      const matches = []
      data.logs.forEach((log) => {
        if (log.raw && log.raw.toLowerCase().includes(keyword.toLowerCase())) {
          // searchMatches 中保存 0-based 原始行索引
          if (typeof log.line === 'number') {
            matches.push(log.line - 1)
          }
        }
      })
      searchMatches.value[service] = matches
      currentMatchIndex.value[service] = matches.length > 0 ? 0 : -1
    } else {
      searchMatches.value[service] = []
      currentMatchIndex.value[service] = -1
    }
    await nextTick()
    scrollLogsToTop()
  } catch (e) {
    console.error('Search logs error:', e)
    showNotification(t('search_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
})

watch(metricsRangeHours, () => {
  updateMetricsCharts()
})

// 跳到上一次浏览位置
const goBackToLastPosition = async () => {
  const service = selectedService.value
  if (!service) return
  const last = logLastPosition.value[service]
  if (!last) return
  logsLoading.value[service] = true
  try {
    const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=${last.offset}`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    const data = await response.json()
    logs.value[service] = data.logs
    logsMeta.value[service] = { total: data.total, offset: data.offset }
    logOffset.value[service] = data.offset
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    await nextTick()
    if (logsContainer.value) {
      logsContainer.value.scrollTop = last.scrollTop || 0
    }
  } catch (e) {
    console.error('Go back position error:', e)
    showNotification(t('jump_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
}

// 在跳转 Top/Bottom 前记录当前浏览位置
const rememberCurrentPosition = () => {
  const service = selectedService.value
  if (!service || !logsContainer.value) return
  logLastPosition.value[service] = {
    offset: logOffset.value[service] || 0,
    scrollTop: logsContainer.value.scrollTop || 0
  }
}

// 基于全局行号跳转到匹配位置
const jumpToLogLine = async (globalIndex) => {
  const service = selectedService.value
  if (!service) return
  // 计算该行所在页的 offset
  const pageSize = 200
  const pageOffset = Math.floor(globalIndex / pageSize) * pageSize
  logsLoading.value[service] = true
  try {
    const response = await authorizedFetch(`/api/logs?service=${service}&lines=${pageSize}&offset=${pageOffset}`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    const data = await response.json()
    logs.value[service] = data.logs
    logsMeta.value[service] = { total: data.total, offset: data.offset }
    logOffset.value[service] = data.offset
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    await nextTick()
    // 计算该行在当前页中的相对 index，并滚动到该行附近
    // globalIndex 是 0-based 原始行索引，data.logs 中带有原始行号 line
    let localIndex = globalIndex - data.offset
    if (Array.isArray(data.logs)) {
      const foundIdx = data.logs.findIndex(l => typeof l.line === 'number' && (l.line - 1) === globalIndex)
      if (foundIdx >= 0) {
        localIndex = foundIdx
      }
    }
    if (logsContainer.value) {
      const container = logsContainer.value
      const lineNode = container.children?.[localIndex]
      if (lineNode) {
        const centerOffset = lineNode.offsetTop - (container.clientHeight / 2) + (lineNode.clientHeight / 2)
        container.scrollTop = Math.max(centerOffset, 0)
      } else {
        const lineHeight = 18 // 估算每行高度（px）
        container.scrollTop = Math.max(0, localIndex * lineHeight - (container.clientHeight / 2))
      }
    }
  } catch (e) {
    console.error('Jump to log line error:', e)
    showNotification(t('jump_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
}

const jumpToNextMatch = () => {
  const service = selectedService.value
  if (!service) return
  const matches = searchMatches.value[service] || []
  if (!matches.length) return
  const current = currentMatchIndex.value[service] ?? -1
  const nextIndex = current < matches.length - 1 ? current + 1 : 0
  currentMatchIndex.value[service] = nextIndex
  jumpToLogLine(matches[nextIndex])
}

const jumpToPrevMatch = () => {
  const service = selectedService.value
  if (!service) return
  const matches = searchMatches.value[service] || []
  if (!matches.length) return
  const current = currentMatchIndex.value[service] ?? 0
  const prevIndex = current > 0 ? current - 1 : matches.length - 1
  currentMatchIndex.value[service] = prevIndex
  jumpToLogLine(matches[prevIndex])
}

// Methods
const refreshStatus = async () => {
  try {
    // Use new dashboard endpoint with system metrics
    const response = await authorizedFetch('/api/dashboard')
    if (!response.ok) throw new Error('Failed to fetch status')
    
    const data = await response.json()
    platformStatus.value = data.platform
    mergeServicesData(data.services)
    systemMetrics.value = data.metrics
    lastUpdated.value = data.timestamp
  statusFetchedAt.value = Date.now()
  statusTicker.value = Date.now()
  } catch (error) {
    if (error.message === 'Unauthorized') return
    console.error('Error refreshing status:', error)
    // Fallback to /api/status if dashboard endpoint is not available
    try {
      const response = await authorizedFetch('/api/status')
      if (!response.ok) throw new Error('Failed to fetch status')
      
      const data = await response.json()
      platformStatus.value = data.platform
      mergeServicesData(data.services)
      lastUpdated.value = data.timestamp
  statusFetchedAt.value = Date.now()
  statusTicker.value = Date.now()
    } catch (fallbackError) {
      if (fallbackError.message === 'Unauthorized') return
      showNotification(t('refresh_failed'), 'error')
    }
  }
}

const loadLogs = async (service) => {
  selectedService.value = service
  logPaused.value = false
  logSearch.value = ''
  logsLoading.value[service] = true
  logs.value[service] = []
  logOffset.value[service] = 0
  logHasMorePrev.value[service] = false
  logHasMoreNext.value[service] = false
  try {
    // 初始加载最新200行
    const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=-200`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    const data = await response.json()
    logs.value[service] = data.logs
    logsMeta.value[service] = { total: data.total, offset: data.offset }
    logOffset.value[service] = data.offset
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    await nextTick()
    scrollLogsToBottom()
    // WebSocket 连接已移至 watch 中管理
    // connectLogWebSocket(service)
  } catch (error) {
    console.error('Error loading logs:', error)
    showNotification(t('logs_load_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
}

// 无限滚动加载更多日志
const fetchMoreLogs = async (direction = 'prev') => {
  const service = selectedService.value
  if (!service) return
  logsLoading.value[service] = true
  const currentLogs = logs.value[service] || []
  const offset = logOffset.value[service] || 0
  let fetchOffset, scrollTo
  if (direction === 'prev' && logHasMorePrev.value[service]) {
    fetchOffset = Math.max(offset - 200, 0)
    scrollTo = 'top'
  } else if (direction === 'next' && logHasMoreNext.value[service]) {
    fetchOffset = offset + currentLogs.length
    scrollTo = 'bottom'
  } else {
    logsLoading.value[service] = false
    return
  }
  try {
    const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=${fetchOffset}`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    const data = await response.json()
    if (direction === 'prev') {
      logs.value[service] = data.logs.concat(currentLogs)
      logOffset.value[service] = data.offset
    } else {
      logs.value[service] = currentLogs.concat(data.logs)
    }
    logsMeta.value[service] = { total: data.total, offset: data.offset }
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    await nextTick()
    if (scrollTo === 'top') scrollLogsToTop()
    if (scrollTo === 'bottom') scrollLogsToBottom()
  } catch (error) {
    showNotification(t('logs_load_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
}

const formatControlDetails = (data) => {
  if (!data) return null
  const parts = []
  if (data.daemon) parts.push('[daemon] running in background')
  if (data.output) parts.push(data.output.trim())
  if (data.stderr) parts.push(`stderr:\n${data.stderr.trim()}`)
  const text = parts.filter(Boolean).join('\n')
  if (!text) return null
  return text.length > 800 ? `${text.slice(0, 800)}\n...` : text
}

const schedulePostControlRefresh = () => {
  // 多次短延迟刷新，避免状态更新滞后
  setTimeout(refreshStatus, 1200)
  setTimeout(refreshStatus, 3000)
  setTimeout(refreshStatus, 6000)
}

const controlService = async (action, service) => {
  controlling.value = true
  try {
    const response = await authorizedFetch('/api/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, service })
    })
    
    if (!response.ok) throw new Error(`Failed to ${action} service`)

    const data = await response.json()
    const details = formatControlDetails(data)
    showNotification(t('service_action_success', { action: t(action) }), 'success', details)
    await refreshStatus()
    schedulePostControlRefresh()
  } catch (error) {
    console.error('Control error:', error)
    showNotification(t('control_failed'), 'error')
  } finally {
    controlling.value = false
  }
}

const togglePause = async () => {
  logPaused.value = !logPaused.value
  if (logSocket && logSocket.readyState === 1) { // 1: OPEN
    logSocket.send(JSON.stringify({ action: logPaused.value ? 'pause' : 'resume' }))
  }
  // 恢复监控时默认回到日志末尾
  if (!logPaused.value) {
    await goToBottom({ keepPaused: true })
  }
}

const downloadLogs = async () => {
  try {
    const response = await authorizedFetch(`/api/logs/download?service=${selectedService.value}`)
    if (!response.ok) throw new Error('Download failed')
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedService.value}-logs-${Date.now()}.log`
    a.click()
    window.URL.revokeObjectURL(url)
    
  showNotification(t('download_success'), 'success')
  } catch (error) {
    console.error('Download error:', error)
    showNotification(t('download_failed'), 'error')
  }
}

const clearLogs = () => {
  logs.value[selectedService.value] = []
}

const getLogColor = (level) => {
  const colors = {
    ERROR: 'text-red-400',
    WARNING: 'text-yellow-300',
    INFO: 'text-green-400',
    DEBUG: 'text-blue-400'
  }
  return colors[level] || 'text-gray-400'
}

// 直达日志底部（最新一页）
const goToBottom = async (options = {}) => {
  const service = selectedService.value
  if (!service) return
  const { keepPaused = false } = options
  if (!keepPaused && !logPaused.value) {
    logPaused.value = true
    if (logSocket && logSocket.readyState === 1) {
      logSocket.send(JSON.stringify({ action: 'pause' }))
    }
  }
  logsLoading.value[service] = true
  try {
    const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=-200`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    const data = await response.json()
    logs.value[service] = data.logs
    logsMeta.value[service] = { total: data.total, offset: data.offset }
    logOffset.value[service] = data.offset
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    await nextTick()
    scrollLogsToBottom()
  } catch (e) {
    console.error('Go to bottom error:', e)
    showNotification(t('jump_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
}

// 直达日志顶部（最前一页）
const goToTop = async () => {
  const service = selectedService.value
  if (!service) return
  if (!logPaused.value) {
    logPaused.value = true
    if (logSocket && logSocket.readyState === 1) {
      logSocket.send(JSON.stringify({ action: 'pause' }))
    }
  }
  logsLoading.value[service] = true
  try {
    const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=0`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    const data = await response.json()
    logs.value[service] = data.logs
    logsMeta.value[service] = { total: data.total, offset: data.offset }
    logOffset.value[service] = data.offset
    logHasMorePrev.value[service] = data.has_more_prev
    logHasMoreNext.value[service] = data.has_more_next
    await nextTick()
    scrollLogsToTop()
  } catch (e) {
    console.error('Go to top error:', e)
    showNotification(t('jump_failed'), 'error')
  } finally {
    logsLoading.value[service] = false
  }
}

const scrollLogsToBottom = () => {
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
}

const scrollLogsToTop = () => {
  if (logsContainer.value) {
    logsContainer.value.scrollTop = 0
  }
}

const attachLogsScrollListener = () => {
  const container = logsContainer.value
  if (!container) return
  const handler = () => {
    const service = selectedService.value
    if (!service) return
    if (container.scrollTop === 0 && logHasMorePrev.value[service]) {
      fetchMoreLogs('prev')
    } else if (
      container.scrollTop + container.clientHeight >= container.scrollHeight - 2 &&
      logHasMoreNext.value[service]
    ) {
      fetchMoreLogs('next')
    }
  }
  container.addEventListener('scroll', handler, { passive: true })
  logsScrollCleanup = () => {
    container.removeEventListener('scroll', handler)
    logsScrollCleanup = null
  }
}

watch(logsContainer, (container) => {
  logsScrollCleanup?.()
  if (container) {
    attachLogsScrollListener()
  }
})

const showNotification = (message, type = 'success', details = null) => {
  notification.value = { message, type, details }
  setTimeout(() => {
    notification.value = null
  }, 3000)
}

const isStatusAlertVisible = (key) => Boolean(statusAlertVisibility.value[key])

const showStatusAlert = (key) => {
  if (!key) return
  statusAlertVisibility.value[key] = true
  if (statusAlertTimers.value[key]) clearTimeout(statusAlertTimers.value[key])
  statusAlertTimers.value[key] = setTimeout(() => {
    statusAlertVisibility.value[key] = false
  }, 5000)
}

const hideStatusAlert = (key) => {
  if (!key) return
  statusAlertVisibility.value[key] = false
  if (statusAlertTimers.value[key]) clearTimeout(statusAlertTimers.value[key])
  delete statusAlertTimers.value[key]
}

const startRepeatAlert = () => {
  if (statusAlertRepeatTimer) return
  statusAlertRepeatTimer = setInterval(() => {
    statusAlerts.value.forEach(alert => {
      showStatusAlert(alert.key)
    })
    if (!statusAlerts.value.length) {
      stopRepeatAlert()
    }
  }, 30000)
}

const stopRepeatAlert = () => {
  if (statusAlertRepeatTimer) clearInterval(statusAlertRepeatTimer)
  statusAlertRepeatTimer = null
}

watch(
  () => statusAlerts.value,
  (alerts) => {
    const activeKeys = new Set(alerts.map(alert => alert.key))
    Object.keys(statusAlertTimers.value).forEach((key) => {
      if (!activeKeys.has(key)) {
        hideStatusAlert(key)
      }
    })

    if (!alerts.length) {
      stopRepeatAlert()
      return
    }

    alerts.forEach(alert => showStatusAlert(alert.key))
    startRepeatAlert()
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  bootstrapSession()
})

onUnmounted(() => {
  cleanupRealtime()
  if (logsInterval) clearInterval(logsInterval)
  logsScrollCleanup?.()
  Object.keys(statusAlertTimers.value).forEach((key) => {
    if (statusAlertTimers.value[key]) clearTimeout(statusAlertTimers.value[key])
  })
  stopRepeatAlert()
  if (focusAlertTimer) clearTimeout(focusAlertTimer)
  closeTerminal()
})
</script>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes grid-move {
  0% {
    background-position: 0 0, 0 0;
  }
  100% {
    background-position: 120px 120px, 120px 120px;
  }
}

@keyframes grid-flicker {
  0%, 100% {
    opacity: 0.55;
  }
  50% {
    opacity: 0.35;
  }
  70% {
    opacity: 0.65;
  }
}

@keyframes scanline-move {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 0 120px;
  }
}

@keyframes scanline-breath {
  0%, 100% {
    opacity: 0.25;
  }
  50% {
    opacity: 0.45;
  }
}

@keyframes noise-flicker {
  0%, 100% {
    opacity: 0.18;
  }
  40% {
    opacity: 0.12;
  }
  60% {
    opacity: 0.22;
  }
}

@keyframes noise-drift {
  0% {
    background-position: 0 0, 16px 24px;
  }
  100% {
    background-position: 40px 60px, 64px 96px;
  }
}

@keyframes star-twinkle {
  0%, 100% {
    opacity: 0.25;
  }
  50% {
    opacity: 0.45;
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.9;
  }
  50% {
    transform: scale(1.35);
    opacity: 0.4;
  }
}

@keyframes float-slow {
  0%, 100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(12px, -16px, 0);
  }
}

@keyframes shimmer-flow {
  0% {
    background-position: -120% 0;
  }
  100% {
    background-position: 120% 0;
  }
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 0.08;
  }
  50% {
    opacity: 0.22;
  }
}

@keyframes alert-pulse {
  0%, 100% {
    box-shadow: 0 0 0 rgba(0, 0, 0, 0);
  }
  50% {
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.2);
  }
}

@keyframes circuit-flow {
  0% {
    background-position: 0 0, 40px 60px, 0 0, 80px 120px;
  }
  100% {
    background-position: 240px 160px, 280px 220px, 200px 240px, 320px 360px;
  }
}

.login-grid {
  background-image:
    linear-gradient(to right, rgba(56, 189, 248, 0.22) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(56, 189, 248, 0.22) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.55;
  animation: grid-move 18s linear infinite, grid-flicker 6s ease-in-out infinite;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.8), transparent 70%);
}

.login-bg-dark {
  background: linear-gradient(135deg, #0b1120 0%, #0f172a 45%, #1e1b4b 100%);
}

.login-bg-light {
  background:
    radial-gradient(circle at 20% 10%, rgba(59, 130, 246, 0.18), transparent 55%),
    radial-gradient(circle at 80% 0%, rgba(99, 102, 241, 0.16), transparent 50%),
    linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.login-grid-light {
  background-image:
    linear-gradient(to right, rgba(59, 130, 246, 0.18) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(59, 130, 246, 0.18) 1px, transparent 1px);
  background-size: 60px 60px;
  opacity: 0.4;
  animation: grid-move 22s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.9), transparent 70%);
}

.login-scanlines-light {
  background-image: repeating-linear-gradient(
    to bottom,
    rgba(59, 130, 246, 0.18) 0px,
    rgba(59, 130, 246, 0.18) 1px,
    rgba(248, 250, 252, 0) 2px,
    rgba(248, 250, 252, 0) 8px
  );
  opacity: 0.28;
  mix-blend-mode: screen;
  animation: scanline-move 12s linear infinite, scanline-breath 7s ease-in-out infinite;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.9), transparent 75%);
}

.login-noise-light {
  background-image:
    radial-gradient(rgba(148, 163, 184, 0.35) 1px, transparent 1px),
    radial-gradient(rgba(59, 130, 246, 0.25) 1.2px, transparent 1.2px);
  background-size: 24px 24px, 36px 36px;
  background-position: 0 0, 18px 28px;
  opacity: 0.2;
  mix-blend-mode: multiply;
  animation: noise-flicker 7s ease-in-out infinite, noise-drift 70s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.85), transparent 75%);
}

.login-orb {
  pointer-events: none;
  animation: float-slow 12s ease-in-out infinite;
}

.login-orb-2 {
  animation-delay: -4s;
}

.login-orb-3 {
  animation-delay: -8s;
}

.login-panel::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(120deg, rgba(56, 189, 248, 0.5), rgba(99, 102, 241, 0.2), rgba(56, 189, 248, 0.4));
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
  opacity: 0.6;
  pointer-events: none;
}

.login-panel::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(120deg, transparent 0%, rgba(255, 255, 255, 0.35) 50%, transparent 100%);
  opacity: 0.2;
  animation: shimmer-flow 8s linear infinite;
  pointer-events: none;
}

.login-shell-dark .login-orb-1 {
  background: rgba(59, 130, 246, 0.3);
}

.login-shell-dark .login-orb-2 {
  background: rgba(34, 211, 238, 0.22);
}

.login-shell-dark .login-orb-3 {
  background: rgba(99, 102, 241, 0.25);
}

.login-shell-light .login-orb-1 {
  background: rgba(59, 130, 246, 0.18);
}

.login-shell-light .login-orb-2 {
  background: rgba(14, 165, 233, 0.18);
}

.login-shell-light .login-orb-3 {
  background: rgba(129, 140, 248, 0.18);
}

.login-scanlines {
  background-image: repeating-linear-gradient(
    to bottom,
    rgba(148, 163, 184, 0.12) 0px,
    rgba(148, 163, 184, 0.12) 1px,
    rgba(15, 23, 42, 0) 2px,
    rgba(15, 23, 42, 0) 6px
  );
  opacity: 0.35;
  mix-blend-mode: screen;
  animation: scanline-move 10s linear infinite, scanline-breath 6s ease-in-out infinite;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.6), transparent 75%);
}

.login-noise {
  background-image:
    radial-gradient(rgba(148, 163, 184, 0.55) 1px, transparent 1px),
    radial-gradient(rgba(56, 189, 248, 0.6) 1px, transparent 1px),
    radial-gradient(rgba(224, 231, 255, 0.7) 1.2px, transparent 1.2px);
  background-size: 16px 16px, 24px 24px, 36px 36px;
  background-position: 0 0, 8px 12px, 18px 28px;
  opacity: 0.32;
  mix-blend-mode: screen;
  animation: star-twinkle 5s ease-in-out infinite, noise-drift 60s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.5), transparent 75%);
}

.tech-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  border-bottom: 1px solid rgba(56, 189, 248, 0.35);
}

.dark .tech-header {
  background: rgba(15, 23, 42, 0.8);
}

.tech-header-line {
  height: 2px;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0), rgba(56, 189, 248, 0.65), rgba(99, 102, 241, 0.6), rgba(56, 189, 248, 0));
  box-shadow: 0 0 18px rgba(56, 189, 248, 0.5);
}

.tech-live-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  background: rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.4);
  color: rgba(56, 189, 248, 0.9);
}

.dark .tech-live-chip {
  background: rgba(15, 23, 42, 0.6);
  color: rgba(125, 211, 252, 0.9);
}

.tech-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.9);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.9);
  animation: pulse 2s ease-in-out infinite;
}

.tech-shell {
  position: relative;
  z-index: 1;
}

.tech-shell::before {
  content: '';
  position: absolute;
  inset: -60px;
  background: radial-gradient(circle at 20% 10%, rgba(56, 189, 248, 0.2), transparent 55%),
    radial-gradient(circle at 80% 0%, rgba(99, 102, 241, 0.18), transparent 50%);
  pointer-events: none;
  z-index: -2;
}

.tech-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(to right, rgba(148, 163, 184, 0.15) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(148, 163, 184, 0.15) 1px, transparent 1px);
  background-size: 120px 120px;
  opacity: 0.35;
  pointer-events: none;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.9), transparent 70%);
  z-index: -2;
  animation: shimmer-flow 24s linear infinite;
}

.tech-ornament {
  position: absolute;
  top: -16px;
  right: 0;
  width: 220px;
  height: 80px;
  background: linear-gradient(120deg, rgba(56, 189, 248, 0.35), rgba(99, 102, 241, 0.1), transparent 70%);
  border-radius: 0 0 0 60px;
  filter: blur(0.2px);
  opacity: 0.75;
  pointer-events: none;
}

.tech-card {
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(56, 189, 248, 0.32);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.18), 0 12px 28px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(10px);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.tech-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.12), transparent 35%, rgba(99, 102, 241, 0.12));
  opacity: 0.6;
  pointer-events: none;
}

.tech-card::after {
  content: '';
  position: absolute;
  top: -40%;
  left: -10%;
  width: 60%;
  height: 200%;
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.35), transparent 70%);
  opacity: 0.18;
  transform: rotate(12deg);
  pointer-events: none;
}

.tech-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.28), 0 18px 36px rgba(15, 23, 42, 0.15);
}

.alert-critical {
  background: linear-gradient(135deg, rgba(254, 226, 226, 0.95), rgba(254, 202, 202, 0.9));
}

.dark .alert-critical {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.8), rgba(88, 28, 28, 0.75));
}

.alert-warning {
  background: linear-gradient(135deg, rgba(254, 249, 195, 0.95), rgba(254, 240, 138, 0.9));
}

.dark .alert-warning {
  background: linear-gradient(135deg, rgba(113, 63, 18, 0.75), rgba(120, 53, 15, 0.7));
}

.alert-pulse {
  animation: alert-pulse 4s ease-in-out infinite;
}

.service-focus {
  position: relative;
  border-color: rgba(56, 189, 248, 0.55);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.25), 0 12px 26px rgba(15, 23, 42, 0.16);
  overflow: hidden;
  transform-style: preserve-3d;
  animation: service-focus-flip 3.2s ease-in-out infinite;
}

.service-focus::before {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  top: -1px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0), rgba(56, 189, 248, 0.55), rgba(99, 102, 241, 0.45), rgba(56, 189, 248, 0));
  opacity: 0.7;
  pointer-events: none;
}

.service-focus::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at 20% 0%, rgba(56, 189, 248, 0.18), transparent 60%);
  opacity: 0.55;
  pointer-events: none;
}


@keyframes service-focus-flip {
  0%, 100% {
    transform: perspective(900px) rotateX(0deg) rotateY(0deg);
    box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.2), 0 10px 22px rgba(15, 23, 42, 0.12);
  }
  50% {
    transform: perspective(900px) rotateX(4deg) rotateY(-5deg);
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.45), 0 18px 32px rgba(15, 23, 42, 0.22);
  }
}

.dark .tech-card {
  background: rgba(15, 23, 42, 0.72);
  border-color: rgba(148, 163, 184, 0.25);
  box-shadow: 0 16px 32px rgba(2, 6, 23, 0.45);
}

.dark .tech-card::before {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), transparent 40%, rgba(99, 102, 241, 0.16));
  opacity: 0.45;
}

.dark .tech-card::after {
  background: linear-gradient(120deg, rgba(148, 163, 184, 0.3), transparent 70%);
  opacity: 0.2;
}

.auth-gradient-light {
  background:
    radial-gradient(circle at top, rgba(59, 130, 246, 0.22), transparent 60%),
    radial-gradient(circle at 20% 30%, rgba(14, 165, 233, 0.2), transparent 55%),
    radial-gradient(circle at 80% 0%, rgba(99, 102, 241, 0.16), transparent 50%),
    linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.auth-grid-light {
  background-image:
    linear-gradient(to right, rgba(148, 163, 184, 0.18) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(148, 163, 184, 0.18) 1px, transparent 1px);
  background-size: 72px 72px;
  opacity: 0.45;
  animation: grid-move 26s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.9), transparent 70%);
}

.auth-scanlines-light {
  background-image: repeating-linear-gradient(
    to bottom,
    rgba(56, 189, 248, 0.22) 0px,
    rgba(56, 189, 248, 0.22) 1px,
    rgba(248, 250, 252, 0) 2px,
    rgba(248, 250, 252, 0) 9px
  );
  opacity: 0.3;
  mix-blend-mode: screen;
  animation: scanline-move 14s linear infinite, scanline-breath 8s ease-in-out infinite;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.9), transparent 75%);
}

.auth-circuit-light {
  background-image:
    linear-gradient(90deg, rgba(59, 130, 246, 0.16) 1px, transparent 1px),
    linear-gradient(180deg, rgba(59, 130, 246, 0.12) 1px, transparent 1px),
    radial-gradient(circle at 20% 30%, rgba(56, 189, 248, 0.35) 1px, transparent 2px),
    radial-gradient(circle at 70% 60%, rgba(99, 102, 241, 0.3) 1px, transparent 2px);
  background-size: 140px 140px, 140px 140px, 220px 220px, 260px 260px;
  background-position: 0 0, 40px 60px, 0 0, 80px 120px;
  opacity: 0.35;
  animation: circuit-flow 26s linear infinite;
  mix-blend-mode: multiply;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.9), transparent 72%);
}

.auth-circuit-dark {
  background-image:
    linear-gradient(90deg, rgba(56, 189, 248, 0.08) 1px, transparent 1px),
    linear-gradient(180deg, rgba(56, 189, 248, 0.06) 1px, transparent 1px);
  background-size: 160px 160px;
  opacity: 0.18;
  animation: circuit-flow 30s linear infinite;
  mix-blend-mode: screen;
}

.auth-noise-light {
  background-image:
    radial-gradient(rgba(148, 163, 184, 0.3) 1px, transparent 1px),
    radial-gradient(rgba(59, 130, 246, 0.28) 1.2px, transparent 1.2px);
  background-size: 26px 26px, 42px 42px;
  background-position: 0 0, 20px 32px;
  opacity: 0.22;
  mix-blend-mode: multiply;
  animation: noise-flicker 6s ease-in-out infinite, noise-drift 80s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.8), transparent 75%);
}

.auth-pulse {
  background: radial-gradient(circle at 50% 30%, rgba(56, 189, 248, 0.25), transparent 60%);
  opacity: 0.12;
  animation: pulse-glow 6s ease-in-out infinite;
  pointer-events: none;
}

.glass-button {
  backdrop-filter: blur(10px);
  border-color: rgba(148, 163, 184, 0.5);
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.12);
}

.dark .glass-button {
  background: rgba(15, 23, 42, 0.6);
  border-color: rgba(148, 163, 184, 0.25);
}

.glass-button-solid {
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 10px 22px rgba(59, 130, 246, 0.18);
}

.dark .glass-button-solid {
  border-color: rgba(148, 163, 184, 0.25);
}

.auth-gradient-dark {
  background:
    radial-gradient(circle at top, rgba(30, 64, 175, 0.35), transparent 60%),
    radial-gradient(circle at 20% 30%, rgba(56, 189, 248, 0.25), transparent 55%),
    linear-gradient(135deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.96));
}

.auth-grid-dark {
  background-image:
    linear-gradient(to right, rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(148, 163, 184, 0.12) 1px, transparent 1px);
  background-size: 64px 64px;
  opacity: 0.35;
  animation: grid-move 26s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.85), transparent 70%);
}

.auth-scanlines-dark {
  background-image: repeating-linear-gradient(
    to bottom,
    rgba(148, 163, 184, 0.1) 0px,
    rgba(148, 163, 184, 0.1) 1px,
    rgba(2, 6, 23, 0) 2px,
    rgba(2, 6, 23, 0) 8px
  );
  opacity: 0.25;
  mix-blend-mode: screen;
  animation: scanline-move 18s linear infinite, scanline-breath 10s ease-in-out infinite;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.7), transparent 78%);
}

.auth-noise-dark {
  background-image:
    radial-gradient(rgba(148, 163, 184, 0.3) 1px, transparent 1px),
    radial-gradient(rgba(59, 130, 246, 0.25) 1.2px, transparent 1.2px);
  background-size: 22px 22px, 36px 36px;
  background-position: 0 0, 18px 28px;
  opacity: 0.22;
  mix-blend-mode: screen;
  animation: noise-flicker 6s ease-in-out infinite, noise-drift 80s linear infinite;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.5), transparent 75%);
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

/* ---- 服务卡片拖拽排序 ---- */
.service-draggable {
  cursor: grab;
  user-select: none;
}
.service-draggable:active {
  cursor: grabbing;
}
.drag-ghost {
  opacity: 0.35 !important;
  transform: scale(0.96);
  box-shadow: none !important;
}
.drag-over {
  outline: 2px dashed rgba(99, 102, 241, 0.7);
  outline-offset: 2px;
  box-shadow: 0 0 16px rgba(99, 102, 241, 0.25);
  transition: outline 0.15s, box-shadow 0.15s;
}
.dark .drag-over {
  outline-color: rgba(129, 140, 248, 0.8);
  box-shadow: 0 0 20px rgba(129, 140, 248, 0.2);
}

/* ---- 终端窗口控制按钮 ---- */
.term-win-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 24px;
  border-radius: 4px;
  color: #9ca3af;
  transition: background 0.15s, color 0.15s;
}
.term-win-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #e5e7eb;
}
</style>
