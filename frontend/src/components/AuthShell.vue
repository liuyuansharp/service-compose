<template>
  <div class="relative min-h-screen overflow-hidden">
    <div :class="isDark ? 'auth-gradient-dark' : 'auth-gradient-light'" class="absolute inset-0"></div>
    <div :class="isDark ? 'auth-grid-dark' : 'auth-grid-light'" class="absolute inset-0"></div>
    <div :class="isDark ? 'auth-scanlines-dark' : 'auth-scanlines-light'" class="absolute inset-0"></div>
    <div :class="isDark ? 'auth-circuit-dark' : 'auth-circuit-light'" class="absolute inset-0"></div>
    <div class="absolute inset-0 auth-pulse"></div>
    <div :class="isDark ? 'auth-noise-dark' : 'auth-noise-light'" class="absolute inset-0"></div>

    <StatusAlertStack
      :status-alerts="statusAlerts"
      :is-status-alert-visible="isStatusAlertVisible"
      :focus-alert-target="focusAlertTarget"
      :hide-status-alert="hideStatusAlert"
      :t="t"
    />

    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup>
import StatusAlertStack from './StatusAlertStack.vue'

defineProps({
  isDark: { type: Boolean, required: true },
  statusAlerts: { type: Array, required: true },
  isStatusAlertVisible: { type: Function, required: true },
  focusAlertTarget: { type: Function, required: true },
  hideStatusAlert: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
