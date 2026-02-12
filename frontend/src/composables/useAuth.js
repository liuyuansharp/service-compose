import { ref, reactive, computed, watch } from 'vue'

export function useAuth({ buildApiUrl, showNotification, t, onLoginSuccess, onLogoutCleanup, onUnauthorized } = {}) {
  const authToken = ref(localStorage.getItem('authToken') || '')
  let storedUser = null
  try {
    storedUser = localStorage.getItem('authUser')
  } catch (e) {
    storedUser = null
  }
  const currentUser = ref(storedUser ? JSON.parse(storedUser) : null)
  const loginForm = reactive({ username: '', password: '' })
  const loginError = ref('')
  const loginLoading = ref(false)

  const isAuthenticated = computed(() => Boolean(authToken.value))
  const userRole = computed(() => currentUser.value?.role || 'readonly')
  const isAdmin = computed(() => userRole.value === 'admin')
  const canOperate = computed(() => userRole.value === 'admin' || userRole.value === 'operator')

  const authorizedFetch = async (url, options = {}) => {
    if (!authToken.value) throw new Error('Not authenticated')
    const headers = new Headers(options.headers || {})
    if (!headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${authToken.value}`)
    }
    const response = await fetch(buildApiUrl(url), { ...options, headers })
    if (response.status === 401) {
      handleUnauthorized()
      throw new Error('Unauthorized')
    }
    if (response.status === 403) {
      showNotification?.(t?.('permission_denied') || 'Permission denied', 'error')
      throw new Error('Permission denied')
    }
    return response
  }

  const handleLogin = async () => {
    loginError.value = ''
    if (!loginForm.username || !loginForm.password) {
      loginError.value = t?.('login_required') || 'Login required'
      return
    }
    loginLoading.value = true
    try {
      const response = await fetch(buildApiUrl('/api/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      })
      const data = await response.json().catch(() => null)
      if (!response.ok) {
        const message = data?.detail || t?.('login_failed') || 'Login failed'
        throw new Error(message)
      }
      authToken.value = data.token
      currentUser.value = data.user
      loginForm.password = ''
      showNotification?.(t?.('welcome_back') || 'Welcome', 'success')
      if (onLoginSuccess) await onLoginSuccess()
    } catch (error) {
      loginError.value = error.message || t?.('login_failed') || 'Login failed'
    } finally {
      loginLoading.value = false
    }
  }

  const logout = (silent = false) => {
    onLogoutCleanup?.()
    authToken.value = ''
    currentUser.value = null
    loginForm.password = ''
    if (!silent) {
      showNotification?.(t?.('logged_out') || 'Logged out', 'success')
    }
  }

  const handleUnauthorized = () => {
    if (!authToken.value) return
    logout(true)
    onUnauthorized?.()
    showNotification?.(t?.('session_expired') || 'Session expired', 'error')
  }

  watch(authToken, (token) => {
    if (token) {
      localStorage.setItem('authToken', token)
    } else {
      localStorage.removeItem('authToken')
    }
  })

  watch(currentUser, (user) => {
    if (user) {
      localStorage.setItem('authUser', JSON.stringify(user))
    } else {
      localStorage.removeItem('authUser')
    }
  })

  return {
    authToken,
    currentUser,
    loginForm,
    loginError,
    loginLoading,
    isAuthenticated,
    userRole,
    isAdmin,
    canOperate,
    authorizedFetch,
    handleLogin,
    logout,
    handleUnauthorized,
  }
}
