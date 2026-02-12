<template>
  <Teleport to="body">
    <div
      v-if="notification"
      class="fixed bottom-4 right-4 p-4 rounded-md border border-black/10 dark:border-white/10 text-white z-40 animate-slide-up"
      :class="notification.type === 'success' ? 'bg-green-600' : 'bg-red-600'"
    >
      {{ notification.message }}
      <div v-if="notification.details" class="mt-2 text-xs font-mono whitespace-pre-wrap bg-black/20 p-2 rounded max-h-40 overflow-auto">
        {{ notification.details }}
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  notification: { type: Object, required: false },
})
</script>
