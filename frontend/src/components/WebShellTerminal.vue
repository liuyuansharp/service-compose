<template>
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
        <button @click.stop="terminalMode = 'normal'" class="text-gray-400 hover:text-white p-0.5" :title="t('terminal_restore')">
          <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" />
          </svg>
        </button>
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
    :class="terminalMode === 'maximized' ? 'inset-0' : 'inset-0 flex items-center justify-center p-2 sm:p-4'"
    @click.self="terminalMode === 'normal' ? (terminalMode = 'minimized') : null"
  >
    <div v-if="terminalMode === 'normal'" class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="terminalMode = 'minimized'"></div>

    <div
      class="relative flex flex-col bg-[#1e1e1e] border border-gray-700 shadow-2xl overflow-hidden"
      :class="terminalMode === 'maximized'
        ? 'w-full h-full'
        : 'rounded-lg w-full max-w-5xl h-[85vh] sm:h-[75vh]'"
    >
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
          <button
            v-if="!terminalConnected"
            @click="connectTerminal"
            class="px-2 py-0.5 text-[10px] bg-blue-600 text-white rounded hover:bg-blue-700 transition mr-1"
          >
            {{ t('terminal_reconnect') }}
          </button>
          <button @click="popoutTerminal" class="term-win-btn" :title="t('terminal_popout')">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </button>
          <button @click="terminalMode = 'minimized'" class="term-win-btn" :title="t('terminal_minimize')">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="18" x2="19" y2="18" />
            </svg>
          </button>
          <button @click="terminalMode = terminalMode === 'maximized' ? 'normal' : 'maximized'" class="term-win-btn" :title="terminalMode === 'maximized' ? t('terminal_restore') : t('terminal_maximize')">
            <svg v-if="terminalMode !== 'maximized'" viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
            </svg>
            <svg v-else viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="5" y="7" width="14" height="14" rx="2" />
              <path d="M9 7V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2" />
            </svg>
          </button>
          <button @click="closeTerminal" class="term-win-btn hover:!bg-red-600 hover:!text-white" :title="t('close')">
            <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18" /><path d="M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <div :ref="(el) => { if (terminalContainerRef) terminalContainerRef.value = el }" class="flex-1 overflow-hidden"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  showTerminal: { type: Boolean, required: true },
  terminalMode: { type: String, required: true },
  terminalConnected: { type: Boolean, required: true },
  terminalContainerRef: { type: Object, default: null },
  connectTerminal: { type: Function, required: true },
  closeTerminal: { type: Function, required: true },
  popoutTerminal: { type: Function, required: true },
  t: { type: Function, required: true },
})
</script>
