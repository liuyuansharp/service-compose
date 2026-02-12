<template>
  <!-- User Management Modal -->
  <div
    v-if="showUserManagement"
    class="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4"
    @click.self="onClose"
  >
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="onClose"></div>
    <div class="relative w-full max-w-4xl max-h-[92vh] sm:max-h-[85vh] flex flex-col bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-lg bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="9" cy="7" r="3" /><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" /><path d="M19 8v6" /><path d="M16 11h6" />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('user_management') }}</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('user_management_desc') }}</p>
          </div>
        </div>
        <button @click="onClose" class="text-gray-400 hover:text-gray-600 dark:hover:text-white p-1">
          <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-4 sm:p-6">
        <div class="mb-6 p-3 sm:p-4 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-slate-800/50">
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 8v6"/><path d="M16 11h6"/><circle cx="9" cy="7" r="3"/><path d="M3 21v-2a4 4 0 0 1 4-4h4"/></svg>
            {{ t('add_user') }}
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 sm:gap-3">
            <input v-model="newUserForm.username" type="text" :placeholder="t('username')" class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            <input v-model="newUserForm.password" type="password" :placeholder="t('password')" class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            <select v-model="newUserForm.role" class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="admin">{{ t('role_admin') }}</option>
              <option value="operator">{{ t('role_operator') }}</option>
              <option value="readonly">{{ t('role_readonly') }}</option>
            </select>
            <button @click="createUser" :disabled="!newUserForm.username || !newUserForm.password" class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition inline-flex items-center justify-center gap-1.5">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
              {{ t('add') }}
            </button>
          </div>
        </div>

        <div class="overflow-x-auto -mx-4 sm:mx-0">
          <table class="w-full text-sm min-w-[600px] sm:min-w-0">
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
              <tr v-for="u in userList" :key="u.id" class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition">
                <td class="py-3 px-4">
                  <div class="flex items-center gap-2">
                    <span class="h-7 w-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-semibold">{{ u.username.charAt(0).toUpperCase() }}</span>
                    <span class="font-medium text-gray-900 dark:text-white">{{ u.username }}</span>
                    <span v-if="u.username === currentUser?.username" class="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-700">{{ t('current_user_tag') }}</span>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <select v-if="editingUserId !== u.id" :value="u.role" @change="quickUpdateRole(u, $event.target.value)" :disabled="u.username === currentUser?.username" class="px-2 py-1 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-slate-800 text-xs text-gray-800 dark:text-gray-200 focus:outline-none" :class="u.username === currentUser?.username ? 'opacity-50 cursor-not-allowed' : ''">
                    <option value="admin">{{ t('role_admin') }}</option>
                    <option value="operator">{{ t('role_operator') }}</option>
                    <option value="readonly">{{ t('role_readonly') }}</option>
                  </select>
                </td>
                <td class="py-3 px-4">
                  <button @click="openVisibleCardsEditor(u)" class="text-xs text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1">
                    <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>
                    {{ u.visible_cards.length ? t('visible_cards_custom', { count: u.visible_cards.length }) : t('visible_cards_all') }}
                  </button>
                </td>
                <td class="py-3 px-4 text-xs text-gray-500 dark:text-gray-400">{{ u.created_at ? u.created_at.slice(0, 10) : '—' }}</td>
                <td class="py-3 px-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button @click="openResetPassword(u)" class="text-xs text-amber-600 dark:text-amber-400 hover:underline">{{ t('reset_password') }}</button>
                    <button v-if="u.username !== currentUser?.username" @click="deleteUser(u)" class="text-xs text-red-600 dark:text-red-400 hover:underline">{{ t('delete') }}</button>
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
    class="fixed inset-0 z-[60] flex items-center justify-center p-2 sm:p-4"
    @click.self="onCloseVisibleCards"
  >
    <div class="absolute inset-0 bg-black/40" @click="onCloseVisibleCards"></div>
    <div class="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h4 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('visible_cards_title', { user: editingVisibleUser?.username }) }}</h4>
  <button @click="onCloseVisibleCards" class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-6">
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{{ t('visible_cards_hint') }}</p>
        <div class="space-y-2.5">
          <label v-for="card in allCardOptions" :key="card.value" class="flex items-center gap-3 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer transition">
            <input type="checkbox" :checked="editingVisibleCards.includes(card.value)" @change="toggleVisibleCard(card.value)" class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500" />
            <div>
              <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ card.label }}</span>
              <p class="text-[11px] text-gray-500 dark:text-gray-400">{{ card.desc }}</p>
            </div>
          </label>
        </div>
        <div class="mt-5 flex items-center justify-between">
          <button @click="onUpdateEditingVisibleCards([])" class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">{{ t('visible_cards_select_all') }}</button>
          <div class="flex gap-2">
            <button @click="onCloseVisibleCards" class="px-4 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800">{{ t('cancel') }}</button>
            <button @click="saveVisibleCards" class="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">{{ t('save') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Reset Password Sub-Modal -->
  <div
    v-if="showResetPassword"
    class="fixed inset-0 z-[60] flex items-center justify-center p-2 sm:p-4"
    @click.self="onCloseResetPassword"
  >
    <div class="absolute inset-0 bg-black/40" @click="onCloseResetPassword"></div>
    <div class="relative w-full max-w-sm bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h4 class="text-base font-semibold text-gray-900 dark:text-white">{{ t('reset_password_title', { user: resetPasswordUser?.username }) }}</h4>
      </div>
      <div class="p-6 space-y-4">
        <input v-model="resetPasswordModel" type="password" :placeholder="t('new_password')" class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
        <div class="flex justify-end gap-2">
          <button @click="onCloseResetPassword" class="px-4 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800">{{ t('cancel') }}</button>
          <button @click="doResetPassword" :disabled="!resetPasswordValue" class="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-40">{{ t('confirm') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  showUserManagement: { type: Boolean, required: true },
  userList: { type: Array, required: true },
  newUserForm: { type: Object, required: true },
  currentUser: { type: [Object, null], default: null },
  editingUserId: { type: [Number, String, null], default: null },
  showVisibleCardsEditor: { type: Boolean, required: true },
  editingVisibleUser: { type: [Object, null], default: null },
  editingVisibleCards: { type: Array, required: true },
  allCardOptions: { type: Array, required: true },
  showResetPassword: { type: Boolean, required: true },
  resetPasswordUser: { type: [Object, null], default: null },
  resetPasswordValue: { type: String, required: true },
  createUser: { type: Function, required: true },
  quickUpdateRole: { type: Function, required: true },
  deleteUser: { type: Function, required: true },
  openVisibleCardsEditor: { type: Function, required: true },
  toggleVisibleCard: { type: Function, required: true },
  saveVisibleCards: { type: Function, required: true },
  openResetPassword: { type: Function, required: true },
  doResetPassword: { type: Function, required: true },
  onClose: { type: Function, required: true },
  onCloseVisibleCards: { type: Function, required: true },
  onCloseResetPassword: { type: Function, required: true },
  onUpdateResetPassword: { type: Function, required: true },
  onUpdateEditingVisibleCards: { type: Function, required: true },
  t: { type: Function, required: true },
})

const resetPasswordModel = computed({
  get: () => props.resetPasswordValue,
  set: (value) => props.onUpdateResetPassword(value),
})
</script>
