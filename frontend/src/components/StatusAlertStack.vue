<template>
  <div
    v-if="statusAlerts.length"
    class="fixed top-4 right-2 sm:right-4 z-50 w-[280px] sm:w-[320px] max-w-[calc(100vw-1rem)] flex flex-col gap-3"
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
</template>

<script setup>
defineProps({
  statusAlerts: { type: Array, required: true },
  isStatusAlertVisible: { type: Function, required: true },
  focusAlertTarget: { type: Function, required: true },
  hideStatusAlert: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
