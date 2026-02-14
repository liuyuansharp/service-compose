<template>
  <div
    v-if="visible"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="$emit('close')"
  >
    <div class="tech-card rounded-md w-full max-w-2xl max-h-[90vh] sm:max-h-[85vh] flex flex-col">
      <div class="flex justify-between items-center p-4 sm:p-5 border-b border-gray-200 dark:border-slate-800">
        <div class="flex items-center gap-2">
          <span class="h-8 w-8 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8" /><path d="M12 17v4" />
            </svg>
          </span>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-slate-100">{{ t('sysinfo_title') }}</h3>
            <p class="text-xs text-gray-500 dark:text-slate-400">{{ info.hostname || '—' }}</p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl leading-none"
        >✕</button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 sm:p-5 bg-gray-50 dark:bg-slate-950">
        <div v-if="loading" class="flex items-center justify-center py-16">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>

        <div v-else-if="error" class="text-sm text-red-500 text-center py-10">{{ error }}</div>

        <div v-else class="space-y-4">
          <!-- OS Section -->
          <section class="tech-card rounded-lg p-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8" /><path d="M12 17v4" /></svg>
              {{ t('sysinfo_os') }}
            </h4>
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
              <div v-for="row in osRows" :key="row.label" class="flex items-baseline gap-2">
                <dt class="text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap min-w-[5rem]">{{ row.label }}</dt>
                <dd class="text-sm font-mono text-gray-800 dark:text-slate-200 truncate">{{ row.value || '—' }}</dd>
              </div>
            </dl>
          </section>

          <!-- CPU Section -->
          <section class="tech-card rounded-lg p-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M7 8h10"/><path d="M9 16h6"/></svg>
              {{ t('sysinfo_cpu') }}
            </h4>
            <dl class="grid grid-cols-1 gap-y-2">
              <div class="flex items-baseline gap-2">
                <dt class="text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap min-w-[5rem]">{{ t('sysinfo_cpu_model') }}</dt>
                <dd class="text-sm font-mono text-gray-800 dark:text-slate-200 truncate">{{ info.cpu_model || '—' }}</dd>
              </div>
            </dl>
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 mt-2">
              <div v-for="row in cpuRows" :key="row.label" class="flex items-baseline gap-2">
                <dt class="text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap min-w-[5rem]">{{ row.label }}</dt>
                <dd class="text-sm font-mono text-gray-800 dark:text-slate-200 truncate">{{ row.value || '—' }}</dd>
              </div>
            </dl>
          </section>

          <!-- Memory Section -->
          <section class="tech-card rounded-lg p-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 7h14"/><path d="M5 12h10"/><path d="M5 17h7"/></svg>
              {{ t('sysinfo_memory') }}
            </h4>
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
              <div v-for="row in memRows" :key="row.label" class="flex items-baseline gap-2">
                <dt class="text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap min-w-[5rem]">{{ row.label }}</dt>
                <dd class="text-sm font-mono text-gray-800 dark:text-slate-200 truncate">{{ row.value || '—' }}</dd>
              </div>
            </dl>
          </section>

          <!-- Network Section -->
          <section v-if="info.network && info.network.length" class="tech-card rounded-lg p-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              {{ t('sysinfo_network') }}
            </h4>
            <div class="space-y-2.5">
              <div
                v-for="net in info.network"
                :key="net.interface"
                class="rounded-md bg-gray-100/70 dark:bg-slate-900/50 border border-gray-200/60 dark:border-slate-800/60 px-3 py-2.5"
              >
                <div class="flex items-center justify-between">
                  <span class="text-xs font-mono font-semibold text-gray-700 dark:text-slate-200">{{ net.interface }}</span>
                  <span class="text-xs font-mono text-gray-500 dark:text-slate-400">{{ net.ip }}</span>
                </div>
              </div>
            </div>
          </section>

          <!-- Runtime Section -->
          <section class="tech-card rounded-lg p-4">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
              {{ t('sysinfo_runtime') }}
            </h4>
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
              <div v-for="row in runtimeRows" :key="row.label" class="flex items-baseline gap-2">
                <dt class="text-xs text-gray-500 dark:text-slate-400 whitespace-nowrap min-w-[5rem]">{{ row.label }}</dt>
                <dd class="text-sm font-mono text-gray-800 dark:text-slate-200 truncate">{{ row.value || '—' }}</dd>
              </div>
            </dl>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, required: true },
  authorizedFetch: { type: Function, required: true },
  t: { type: Function, required: true },
})

defineEmits(['close'])

const info = ref({})
const loading = ref(false)
const error = ref('')

const fetchInfo = async () => {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await props.authorizedFetch('/api/system-info')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    info.value = await res.json()
  } catch (e) {
    error.value = e.message || 'Failed to load'
  } finally {
    loading.value = false
  }
}

watch(() => props.visible, (v) => {
  if (v) fetchInfo()
})

const formatBootTime = (iso) => {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

const osRows = computed(() => [
  { label: props.t('sysinfo_distro'), value: info.value.distro },
  { label: props.t('sysinfo_kernel'), value: info.value.kernel },
  { label: props.t('sysinfo_arch'), value: info.value.arch },
  { label: props.t('sysinfo_glibc'), value: info.value.glibc },
  { label: props.t('sysinfo_hostname'), value: info.value.hostname },
  { label: props.t('sysinfo_uptime'), value: info.value.uptime },
])

const cpuRows = computed(() => [
  { label: props.t('sysinfo_cores_physical'), value: String(info.value.cpu_cores_physical ?? '—') },
  { label: props.t('sysinfo_cores_logical'), value: String(info.value.cpu_cores_logical ?? '—') },
  { label: props.t('sysinfo_cpu_freq'), value: info.value.cpu_freq_mhz ? `${info.value.cpu_freq_mhz} MHz` : '—' },
  { label: props.t('sysinfo_load_avg'), value: info.value.load_avg?.length ? info.value.load_avg.join(' / ') : '—' },
])

const memRows = computed(() => [
  { label: props.t('sysinfo_mem_total'), value: info.value.memory_total_gb ? `${info.value.memory_total_gb} GB` : '—' },
  { label: props.t('sysinfo_swap'), value: info.value.swap_total_gb !== undefined ? `${info.value.swap_total_gb} GB` : '—' },
])

const runtimeRows = computed(() => [
  { label: 'Python', value: info.value.python_version },
  { label: props.t('sysinfo_boot_time'), value: formatBootTime(info.value.boot_time) },
])
</script>
