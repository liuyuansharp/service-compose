import { ref } from 'vue'

export function useNotification(t) {
  const notification = ref(null)

  const showNotification = (message, type = 'success', details = null) => {
    notification.value = { message, type, details }
    setTimeout(() => {
      notification.value = null
    }, 3000)
  }

  const confirmDialog = ref({
    show: false,
    type: 'info',
    title: '',
    message: '',
    detail: '',
    confirmText: '',
    cancelText: '',
    onConfirm: null,
  })

  const openConfirmDialog = ({ type = 'info', title, message, detail = '', confirmText, cancelText, onConfirm }) => {
    confirmDialog.value = {
      show: true,
      type,
      title: title || '',
      message: message || '',
      detail,
      confirmText: confirmText || t('confirm_yes'),
      cancelText: cancelText || t('confirm_no'),
      onConfirm,
    }
  }

  const closeConfirmDialog = (confirmed = false) => {
    if (confirmed && confirmDialog.value.onConfirm) {
      confirmDialog.value.onConfirm()
    }
    confirmDialog.value.show = false
  }

  return {
    notification,
    showNotification,
    confirmDialog,
    openConfirmDialog,
    closeConfirmDialog,
  }
}
