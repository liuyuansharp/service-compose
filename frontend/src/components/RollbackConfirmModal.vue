<template>
  <!-- Rollback Confirm Modal -->
  <div
    v-if="rollbackConfirmVisible"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4"
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
</template>

<script setup>
defineProps({
  rollbackConfirmVisible: { type: Boolean, required: true },
  rollbackPendingBackup: { type: [String, null], default: null },
  cancelRollback: { type: Function, required: true },
  confirmRollback: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
