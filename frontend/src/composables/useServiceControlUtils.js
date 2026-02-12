export const useServiceControlUtils = ({ refreshStatus }) => {
  const formatControlDetails = (data) => {
    if (!data) return null
    const parts = []
    if (data.daemon) parts.push('[daemon] running in background')
    if (data.output) parts.push(data.output.trim())
    if (data.stderr) parts.push(`stderr:\n${data.stderr.trim()}`)
    const text = parts.filter(Boolean).join('\n')
    if (!text) return null
    return text.length > 800 ? `${text.slice(0, 800)}\n...` : text
  }

  const schedulePostControlRefresh = () => {
    // 多次短延迟刷新，避免状态更新滞后
    setTimeout(refreshStatus, 1200)
    setTimeout(refreshStatus, 3000)
    setTimeout(refreshStatus, 6000)
  }

  return {
    formatControlDetails,
    schedulePostControlRefresh,
  }
}
