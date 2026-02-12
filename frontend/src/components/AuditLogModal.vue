<template>
  <div
    v-if="showAuditLog"
    class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="onClose"
  >
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="onClose"></div>
    <div class="relative w-full max-w-5xl max-h-[92vh] sm:max-h-[85vh] flex flex-col bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('audit_log') }}</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('audit_log_desc') }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="loadAuditLogs()" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">{{ t('refresh') }}</button>
          <button @click="onClose" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-1">
            <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
          </button>
        </div>
      </div>
      <div class="px-4 sm:px-6 py-3 border-b border-gray-100 dark:border-gray-800 flex flex-wrap items-center gap-2 sm:gap-3 flex-shrink-0">
        <select v-model="auditFilter.action" class="px-2 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-xs text-gray-800 dark:text-gray-200 focus:outline-none">
          <option value="">{{ t('audit_filter_all_actions') }}</option>
          <option value="login">{{ t('audit_action_login') }}</option>
          <option value="start">{{ t('audit_action_start') }}</option>
          <option value="stop">{{ t('audit_action_stop') }}</option>
          <option value="restart">{{ t('audit_action_restart') }}</option>
          <option value="upload">{{ t('audit_action_upload') }}</option>
          <option value="rollback">{{ t('audit_action_rollback') }}</option>
          <option value="create_user">{{ t('audit_action_create_user') }}</option>
          <option value="update_user">{{ t('audit_action_update_user') }}</option>
          <option value="delete_user">{{ t('audit_action_delete_user') }}</option>
          <option value="batch_start">{{ t('audit_action_batch_start') }}</option>
          <option value="batch_stop">{{ t('audit_action_batch_stop') }}</option>
        </select>
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ t('audit_total', { count: auditTotal }) }}</span>
        <span v-if="!isAdmin" class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">{{ t('audit_own_only') }}</span>
      </div>
      <div class="flex-1 overflow-y-auto overflow-x-auto">
        <table class="w-full text-sm min-w-[700px]">
          <thead class="sticky top-0 bg-gray-50 dark:bg-slate-800/80 backdrop-blur-sm z-10">
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_time') }}</th>
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_user') }}</th>
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_role') }}</th>
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_action') }}</th>
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_target') }}</th>
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_detail') }}</th>
              <th class="text-left py-2.5 px-4 font-medium text-gray-600 dark:text-gray-400 text-xs">{{ t('audit_col_result') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, idx) in filteredAuditLogs" :key="idx" class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition">
              <td class="py-2 px-4 text-xs text-gray-500 dark:text-gray-400 font-mono whitespace-nowrap">{{ formatAuditTime(entry.timestamp) }}</td>
              <td class="py-2 px-4">
                <span class="inline-flex items-center gap-1.5">
                  <span class="h-5 w-5 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-[10px] font-semibold flex-shrink-0">{{ entry.user?.charAt(0)?.toUpperCase() || '?' }}</span>
                  <span class="text-xs font-medium text-gray-800 dark:text-gray-200">{{ entry.user }}</span>
                </span>
              </td>
              <td class="py-2 px-4">
                <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="entry.role === 'admin' ? 'bg-red-500/15 text-red-500' : entry.role === 'operator' ? 'bg-blue-500/15 text-blue-500' : 'bg-gray-500/15 text-gray-500'">{{ t('role_' + (entry.role || 'unknown')) }}</span>
              </td>
              <td class="py-2 px-4">
                <span class="text-xs px-2 py-0.5 rounded-md font-medium" :class="auditActionClass(entry.action)">{{ t('audit_action_' + entry.action) || entry.action }}</span>
              </td>
              <td class="py-2 px-4 text-xs text-gray-700 dark:text-gray-300 font-mono max-w-[200px] truncate" :title="entry.target">{{ entry.target || '—' }}</td>
              <td class="py-2 px-4 text-xs text-gray-500 dark:text-gray-400 max-w-[200px] truncate" :title="entry.detail">{{ entry.detail || '—' }}</td>
              <td class="py-2 px-4">
                <span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium" :class="entry.result === 'success' ? 'bg-green-500/15 text-green-600 dark:text-green-400' : 'bg-red-500/15 text-red-600 dark:text-red-400'">{{ entry.result === 'success' ? t('audit_result_success') : t('audit_result_failed') }}</span>
              </td>
            </tr>
            <tr v-if="filteredAuditLogs.length === 0">
              <td colspan="7" class="py-8 text-center text-sm text-gray-400 dark:text-gray-500">{{ t('audit_empty') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="auditTotal > auditLimit" class="px-4 sm:px-6 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
        <button @click="auditOffset = Math.max(0, auditOffset - auditLimit); loadAuditLogs()" :disabled="auditOffset <= 0" class="px-3 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed">{{ t('audit_prev') }}</button>
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ auditOffset + 1 }}–{{ Math.min(auditOffset + auditLimit, auditTotal) }} / {{ auditTotal }}</span>
        <button @click="auditOffset = auditOffset + auditLimit; loadAuditLogs()" :disabled="auditOffset + auditLimit >= auditTotal" class="px-3 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed">{{ t('audit_next') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  showAuditLog: { type: Boolean, required: true },
  filteredAuditLogs: { type: Array, required: true },
  auditTotal: { type: Number, required: true },
  auditOffset: { type: Number, required: true },
  auditLimit: { type: Number, required: true },
  auditFilter: { type: Object, required: true },
  isAdmin: { type: Boolean, required: true },
  loadAuditLogs: { type: Function, required: true },
  formatAuditTime: { type: Function, required: true },
  auditActionClass: { type: Function, required: true },
  onClose: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
