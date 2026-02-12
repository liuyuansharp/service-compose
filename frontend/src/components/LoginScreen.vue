<template>
  <div
    :class="[
      'min-h-screen relative overflow-hidden flex items-center justify-center px-4 py-8 sm:px-6 sm:py-12',
      isDark ? 'login-shell-dark' : 'login-shell-light',
    ]"
  >
    <div :class="isDark ? 'login-bg-dark' : 'login-bg-light'" class="absolute inset-0"></div>
    <div :class="isDark ? 'login-grid' : 'login-grid-light'" class="absolute inset-0"></div>
    <div :class="isDark ? 'login-scanlines' : 'login-scanlines-light'" class="absolute inset-0"></div>
    <div :class="isDark ? 'login-noise' : 'login-noise-light'" class="absolute inset-0"></div>
    <div class="absolute -top-24 -left-24 h-64 w-64 rounded-full blur-3xl login-orb login-orb-1"></div>
    <div class="absolute top-1/3 -right-32 h-72 w-72 rounded-full blur-3xl login-orb login-orb-2"></div>
    <div class="absolute bottom-0 left-1/4 h-52 w-52 rounded-full blur-3xl login-orb login-orb-3"></div>

    <div
      :class="[
        'relative w-full max-w-4xl border backdrop-blur-xl rounded-2xl shadow-2xl login-panel',
        isDark ? 'border-white/10 bg-white/5 dark:bg-slate-900/40' : 'border-slate-200 bg-white/80',
      ]"
    >
      <div class="grid md:grid-cols-2 gap-0">
        <div class="p-5 sm:p-8 md:p-10 border-b md:border-b-0 md:border-r border-white/10">
          <div class="flex items-center justify-between gap-2">
            <div :class="['text-xs uppercase tracking-[0.25em]', isDark ? 'text-blue-200/70' : 'text-slate-500']">
              {{ t('login_tagline') }}
            </div>
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
        <div class="p-5 sm:p-8 md:p-10">
          <div class="mb-6">
            <p :class="['text-xs uppercase tracking-[0.35em]', isDark ? 'text-blue-100/50' : 'text-slate-400']">
              {{ t('login') }}
            </p>
            <h3 :class="['mt-2 text-xl font-semibold', isDark ? 'text-white' : 'text-slate-900']">
              {{ t('welcome_back') }}
            </h3>
            <p :class="['mt-2 text-sm', isDark ? 'text-blue-100/70' : 'text-slate-500']">
              {{ t('login_required') }}
            </p>
          </div>
          <form class="space-y-4" @submit.prevent="handleLogin">
            <div>
              <label :class="['block text-xs font-medium mb-2', isDark ? 'text-blue-100/70' : 'text-slate-600']">
                {{ t('username') }}
              </label>
              <input
                v-model="loginForm.username"
                type="text"
                autocomplete="username"
                :class="[
                  'w-full px-3 py-2.5 rounded-lg focus:ring-2 focus:outline-none',
                  isDark
                    ? 'bg-white/5 border border-white/15 text-white placeholder:text-blue-100/40 focus:ring-cyan-400/70 focus:border-cyan-300/70'
                    : 'bg-white border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:ring-blue-500/40 focus:border-blue-300',
                ]"
                :placeholder="t('username_placeholder')"
              />
            </div>
            <div>
              <label :class="['block text-xs font-medium mb-2', isDark ? 'text-blue-100/70' : 'text-slate-600']">
                {{ t('password') }}
              </label>
              <input
                v-model="loginForm.password"
                type="password"
                autocomplete="current-password"
                :class="[
                  'w-full px-3 py-2.5 rounded-lg focus:ring-2 focus:outline-none',
                  isDark
                    ? 'bg-white/5 border border-white/15 text-white placeholder:text-blue-100/40 focus:ring-cyan-400/70 focus:border-cyan-300/70'
                    : 'bg-white border border-slate-200 text-slate-800 placeholder:text-slate-400 focus:ring-blue-500/40 focus:border-blue-300',
                ]"
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
</template>

<script setup>
defineProps({
  isDark: { type: Boolean, required: true },
  themeLabel: { type: String, required: true },
  langLabel: { type: String, required: true },
  toggleTheme: { type: Function, required: true },
  toggleLanguage: { type: Function, required: true },
  loginForm: { type: Object, required: true },
  loginError: { type: [String, null], default: null },
  loginLoading: { type: Boolean, required: true },
  handleLogin: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
