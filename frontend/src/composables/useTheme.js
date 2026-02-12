import { ref, computed, watch } from 'vue'

export function useTheme(t) {
  const isDark = ref(localStorage.getItem('theme') === 'dark')

  const themeLabel = computed(() => (isDark.value ? t('light_mode') : t('dark_mode')))

  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  watch(isDark, (value) => {
    localStorage.setItem('theme', value ? 'dark' : 'light')
  }, { immediate: true })

  return {
    isDark,
    themeLabel,
    toggleTheme,
  }
}
