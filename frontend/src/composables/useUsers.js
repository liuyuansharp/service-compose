import { ref, reactive, computed } from 'vue'

export function useUsers({ authorizedFetch, showNotification, t, currentUser } = {}) {
  const showUserManagement = ref(false)
  const userList = ref([])
  const newUserForm = reactive({ username: '', password: '', role: 'readonly' })
  const showVisibleCardsEditor = ref(false)
  const editingVisibleUser = ref(null)
  const editingVisibleCards = ref([])
  const editingUserId = ref(null)
  const showResetPassword = ref(false)
  const resetPasswordUser = ref(null)
  const resetPasswordValue = ref('')

  const loadUsers = async () => {
    try {
      const response = await authorizedFetch('/api/users')
      if (response.ok) {
        userList.value = await response.json()
      }
    } catch (e) {
      console.error('Load users error:', e)
    }
  }

  const createUser = async () => {
    try {
      const response = await authorizedFetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUserForm)
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed')
      }
      showNotification?.(t?.('user_created') || 'User created', 'success')
      newUserForm.username = ''
      newUserForm.password = ''
      newUserForm.role = 'readonly'
      await loadUsers()
    } catch (e) {
      showNotification?.(e.message, 'error')
    }
  }

  const quickUpdateRole = async (user, newRole) => {
    try {
      const response = await authorizedFetch(`/api/users/${user.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed')
      }
      showNotification?.(t?.('user_updated') || 'User updated', 'success')
      await loadUsers()
    } catch (e) {
      showNotification?.(e.message, 'error')
      await loadUsers()
    }
  }

  const deleteUser = async (user) => {
    if (!confirm(t?.('delete_user_confirm', { user: user.username }) || `Delete ${user.username}?`)) return
    try {
      const response = await authorizedFetch(`/api/users/${user.id}`, { method: 'DELETE' })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed')
      }
      showNotification?.(t?.('user_deleted') || 'User deleted', 'success')
      await loadUsers()
    } catch (e) {
      showNotification?.(e.message, 'error')
    }
  }

  const openVisibleCardsEditor = (user) => {
    editingVisibleUser.value = user
    editingVisibleCards.value = [...(user.visible_cards || [])]
    showVisibleCardsEditor.value = true
  }

  const toggleVisibleCard = (cardValue) => {
    const idx = editingVisibleCards.value.indexOf(cardValue)
    if (idx >= 0) {
      editingVisibleCards.value.splice(idx, 1)
    } else {
      editingVisibleCards.value.push(cardValue)
    }
  }

  const saveVisibleCards = async () => {
    if (!editingVisibleUser.value) return
    try {
      const response = await authorizedFetch(`/api/users/${editingVisibleUser.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ visible_cards: editingVisibleCards.value })
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed')
      }
      showNotification?.(t?.('user_updated') || 'User updated', 'success')
      showVisibleCardsEditor.value = false
      await loadUsers()
      if (editingVisibleUser.value.username === currentUser?.value?.username) {
        currentUser.value = { ...currentUser.value, visible_cards: [...editingVisibleCards.value] }
      }
    } catch (e) {
      showNotification?.(e.message, 'error')
    }
  }

  const openResetPassword = (user) => {
    resetPasswordUser.value = user
    resetPasswordValue.value = ''
    showResetPassword.value = true
  }

  const doResetPassword = async () => {
    if (!resetPasswordUser.value || !resetPasswordValue.value) return
    try {
      const response = await authorizedFetch(`/api/users/${resetPasswordUser.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: resetPasswordValue.value })
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed')
      }
      showNotification?.(t?.('password_reset_success') || 'Password reset', 'success')
      showResetPassword.value = false
    } catch (e) {
      showNotification?.(e.message, 'error')
    }
  }

  const allCardOptions = computed(() => [])

  return {
    showUserManagement,
    userList,
    newUserForm,
    showVisibleCardsEditor,
    editingVisibleUser,
    editingVisibleCards,
    editingUserId,
    showResetPassword,
    resetPasswordUser,
    resetPasswordValue,
    loadUsers,
    createUser,
    quickUpdateRole,
    deleteUser,
    openVisibleCardsEditor,
    toggleVisibleCard,
    saveVisibleCards,
    openResetPassword,
    doResetPassword,
    allCardOptions,
  }
}
