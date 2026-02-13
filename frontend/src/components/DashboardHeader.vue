<template>
  <header class="tech-header border-b border-white/10">
    <div class="max-w-screen-2xl mx-auto px-3 sm:px-6 lg:px-8 py-3">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <!-- Left: title -->
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

        <!-- Right: toolbar -->
        <div class="flex items-center gap-2 flex-wrap justify-end">
          <!-- Terminal (admin) -->
          <button
            v-if="isAdmin"
            @click="onOpenTerminal"
            class="hdr-btn"
            :title="t('terminal')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" />
            </svg>
            <span class="hidden sm:inline">{{ t('terminal') }}</span>
          </button>

          <!-- Refresh -->
          <button
            @click="refreshStatus"
            class="hdr-icon-btn text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/30 hover:bg-blue-50 dark:hover:bg-blue-500/10"
            :title="t('refresh')"
          >
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 12a8 8 0 1 1-2.34-5.66" /><path d="M20 4v6h-6" />
            </svg>
          </button>

          <!-- Language -->
          <button
            @click="toggleLanguage"
            class="hdr-icon-btn"
            :title="langLabel"
          >
            <span class="text-[11px] font-bold leading-none">{{ langLabel }}</span>
          </button>

          <!-- Theme -->
          <button
            @click="toggleTheme"
            class="hdr-icon-btn"
            :title="themeLabel"
          >
            <!-- Sun (shown in dark mode → click to switch to light) -->
            <svg v-if="isDark" viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
            <!-- Moon (shown in light mode → click to switch to dark) -->
            <svg v-else viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </button>

          <!-- Divider -->
          <span class="hidden sm:block w-px h-5 bg-gray-300 dark:bg-slate-700"></span>

          <!-- Personal Center dropdown -->
          <div class="relative" ref="dropdownRef">
            <button
              @click="showDropdown = !showDropdown"
              class="hdr-btn gap-1.5"
            >
              <span class="h-6 w-6 rounded-full border border-cyan-300/60 dark:border-cyan-400/30 bg-white/60 dark:bg-slate-800/60 shadow-[0_0_8px_rgba(34,211,238,0.3)] flex items-center justify-center flex-shrink-0">
                <svg viewBox="0 0 24 24" class="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-300" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="8" r="3.5" />
                  <path d="M4 20c1.8-3.6 5-5.4 8-5.4s6.2 1.8 8 5.4" />
                </svg>
              </span>
              <span class="text-sm truncate max-w-[72px] sm:max-w-none">{{ currentUser?.username || t('user') }}</span>
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
              <!-- chevron -->
              <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 ml-0.5 transition-transform" :class="showDropdown ? 'rotate-180' : ''" fill="currentColor">
                <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
              </svg>
            </button>

            <!-- Dropdown menu -->
            <Transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="opacity-0 scale-95"
              enter-to-class="opacity-100 scale-100"
              leave-active-class="transition ease-in duration-75"
              leave-from-class="opacity-100 scale-100"
              leave-to-class="opacity-0 scale-95"
            >
              <div
                v-if="showDropdown"
                class="absolute right-0 top-full mt-1.5 w-48 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-800 shadow-xl dark:shadow-black/40 ring-1 ring-black/5 dark:ring-white/5 z-50 py-1 origin-top-right"
              >
                <!-- Header: personal center -->
                <div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
                  <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ t('personal_center') }}</p>
                </div>

                <!-- User Management (admin only) -->
                <button
                  v-if="isAdmin"
                  @click="handleMenuItem(onOpenUserManagement)"
                  class="dropdown-item"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="9" cy="7" r="3" />
                    <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
                    <path d="M19 8v6" /><path d="M16 11h6" />
                  </svg>
                  {{ t('user_management') }}
                </button>

                <!-- Audit Log -->
                <button
                  @click="handleMenuItem(onOpenAuditLog)"
                  class="dropdown-item"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                  {{ t('audit_log') }}
                </button>

                <!-- Divider -->
                <div class="my-1 border-t border-gray-100 dark:border-gray-700"></div>

                <!-- Logout -->
                <button
                  @click="handleMenuItem(onLogout)"
                  class="dropdown-item text-red-500 dark:text-red-400"
                >
                  <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                  {{ t('logout') }}
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
    <div class="tech-header-line"></div>
  </header>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  isAdmin: { type: Boolean, required: true },
  isConnected: { type: Boolean, default: false },
  isDark: { type: Boolean, default: false },
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

const showDropdown = ref(false)
const dropdownRef = ref(null)

function handleMenuItem(fn) {
  showDropdown.value = false
  fn()
}

function onClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside, true))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside, true))
</script>

<style scoped>
.hdr-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid;
  border-color: rgba(209, 213, 219, 0.7);
  color: rgba(75, 85, 99, 1);
  transition: all 0.15s;
}
.hdr-btn:hover {
  background: rgba(243, 244, 246, 1);
}
:deep(.dark) .hdr-btn,
.dark .hdr-btn {
  border-color: rgba(55, 65, 81, 0.7);
  color: rgba(209, 213, 219, 1);
}
:deep(.dark) .hdr-btn:hover,
.dark .hdr-btn:hover {
  background: rgba(31, 41, 55, 1);
}

.hdr-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid;
  border-color: rgba(209, 213, 219, 0.7);
  color: rgba(107, 114, 128, 1);
  transition: all 0.15s;
}
.hdr-icon-btn:hover {
  background: rgba(243, 244, 246, 1);
}
:deep(.dark) .hdr-icon-btn,
.dark .hdr-icon-btn {
  border-color: rgba(55, 65, 81, 0.7);
  color: rgba(156, 163, 175, 1);
}
:deep(.dark) .hdr-icon-btn:hover,
.dark .hdr-icon-btn:hover {
  background: rgba(31, 41, 55, 1);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  color: rgba(55, 65, 81, 1);
  transition: background 0.1s;
  text-align: left;
}
.dropdown-item:hover {
  background: rgba(243, 244, 246, 1);
}
:deep(.dark) .dropdown-item,
.dark .dropdown-item {
  color: rgba(209, 213, 219, 1);
}
:deep(.dark) .dropdown-item:hover,
.dark .dropdown-item:hover {
  background: rgba(31, 41, 55, 1);
}
.dropdown-item.text-red-500:hover,
.dropdown-item.text-red-400:hover {
  background: rgba(254, 242, 242, 1);
}
:deep(.dark) .dropdown-item.text-red-500:hover,
:deep(.dark) .dropdown-item.text-red-400:hover,
.dark .dropdown-item.text-red-500:hover,
.dark .dropdown-item.text-red-400:hover {
  background: rgba(127, 29, 29, 0.15);
}
</style>
