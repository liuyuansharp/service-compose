import { ref, computed, nextTick, watch } from 'vue'

export function useLogs({
  authorizedFetch,
  buildWsUrl,
  t,
  showNotification,
  logsContainer,
  selectedService,
  authToken,
  openConfirmDialog,
}) {
  const logs = ref({})
  const logsLoading = ref({})
  const logsMeta = ref({})
  const logFileSize = ref({})
  const logOffset = ref({})
  const logHasMorePrev = ref({})
  const logHasMoreNext = ref({})
  const logLastPosition = ref({})
  const searchMatches = ref({})
  const currentMatchIndex = ref({})
  const logPaused = ref(false)
  const followLogs = ref(true)
  const highlightedLogLine = ref(null)
  let highlightedLogLineTimer = null
  const logSearch = ref('')
  const logLevelFilter = ref('ALL')
  const LIVE_LOG_LIMIT = 5000
  const logTimeRange = ref('all')
  const logTimeRangeOptions = [
    { value: '1h', label: computed(() => t('range_1h')) },
    { value: '6h', label: computed(() => t('range_6h')) },
    { value: '24h', label: computed(() => t('range_24h')) },
    { value: 'all', label: computed(() => t('range_all')) },
  ]

  const formatFileSize = (bytes) => {
    if (bytes == null || bytes < 0) return ''
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }

  const escapeHtml = (str) => {
    if (!str) return ''
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }
  const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  const logLevelFilters = [
    { value: 'ALL',     label: computed(() => t('log_level_all')),  activeClass: 'bg-white dark:bg-gray-600 text-gray-800 dark:text-white shadow-sm' },
    { value: 'ERROR',   label: 'ERR',      activeClass: 'bg-red-500/90 text-white shadow-sm' },
    { value: 'WARNING', label: 'WARN',     activeClass: 'bg-yellow-500/90 text-white shadow-sm' },
    { value: 'INFO',    label: 'INFO',     activeClass: 'bg-green-500/90 text-white shadow-sm' },
    { value: 'DEBUG',   label: 'DBG',      activeClass: 'bg-blue-500/90 text-white shadow-sm' },
  ]

  const logMode = ref('live')

  const onLogLevelClick = async (level) => {
    logLevelFilter.value = level
    searchMatches.value[selectedService.value] = []
    currentMatchIndex.value[selectedService.value] = -1
    if (logMode.value === 'live') {
      if (logSearch.value) {
        const kw = logSearch.value.toLowerCase()
        const matches = []
        filteredDisplayedLogs.value.forEach((log) => {
          if (log.raw && log.raw.toLowerCase().includes(kw) && log.line != null) {
            matches.push(log.line)
          }
        })
        searchMatches.value[selectedService.value] = matches
        currentMatchIndex.value[selectedService.value] = matches.length > 0 ? 0 : -1
        if (matches.length > 0) {
          await nextTick()
          scrollToSearchMatch(selectedService.value, 0)
        }
      }
      return
    }
    if (level !== 'ALL') {
      await fetchLogsByLevel(level)
    } else {
      await loadLogs(selectedService.value)
    }
    if (logSearch.value) {
      const service = selectedService.value
      const keyword = logSearch.value
      try {
        const params = new URLSearchParams({ service, search: keyword })
        if (level && level !== 'ALL') {
          params.set('level', level)
        }
        const rangeQ = toRangeQuery()
        const response = await authorizedFetch(`/api/logs/search-matches?${params.toString()}${rangeQ}`)
        if (response.ok && logSearch.value === keyword) {
          const data = await response.json()
          const matches = (data.matches || []).map(n => n - 1)
          searchMatches.value[service] = matches
          currentMatchIndex.value[service] = matches.length > 0 ? 0 : -1
          if (matches.length > 0) {
            await scrollToSearchMatch(service, 0)
          }
        }
      } catch (e) {
        console.error('Re-search after level change error:', e)
      }
    }
  }

  const closeLogViewer = () => {
    selectedService.value = null
  }

  const isCurrentMatchLine = (log) => {
    const svc = selectedService.value
    if (!logSearch.value || !svc) return false
    const matches = searchMatches.value[svc]
    const matchIdx = currentMatchIndex.value[svc]
    if (!matches?.length || matchIdx == null || matchIdx < 0) return false
    if (logMode.value === 'live') {
      return matches[matchIdx] === log.line
    }
    const lineNo = getLogLineNumber(log)
    return matches[matchIdx] === (lineNo - 1)
  }

  const getLogLineNumber = (log) => {
    const svc = selectedService.value
    return log.line || ((logsMeta.value[svc]?.offset || 0) + (log._origIdx ?? 0) + 1)
  }

  const onLineNumberClick = (log) => {
    if (logMode.value === 'live') return
    const lineNo = getLogLineNumber(log)
    jumpToLogLine(lineNo - 1)
  }

  const highlightLogText = (text) => {
    if (!text) return ''
    const raw = escapeHtml(text)
    const kw = logSearch.value
    if (!kw) return raw
    try {
      const re = new RegExp(escapeRegExp(kw), 'gi')
      return raw.replace(re, (m) => `<mark class="bg-yellow-300/80 text-black rounded-sm px-0.5">${m}</mark>`)
    } catch (e) {
      return raw
    }
  }

  const onLogsScroll = () => {
    const container = logsContainer.value
    if (!container) return
    const svc = selectedService.value
    if (!svc) return

    if (logMode.value === 'live') {
      const atBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 30
      followLogs.value = atBottom
    } else {
      if (logsLoading.value[svc]) return
      if (container.scrollTop === 0 && logHasMorePrev.value[svc]) {
        fetchMoreLogs('prev')
      } else if (container.scrollTop + container.clientHeight >= container.scrollHeight - 2 && logHasMoreNext.value[svc]) {
        fetchMoreLogs('next')
      }
    }
  }

  const fetchLogsByLevel = async (level) => {
    const service = selectedService.value
    if (!service) return
    logsLoading.value[service] = true
    try {
      const params = new URLSearchParams({ service, lines: '200', offset: '-200', level })
      const response = await authorizedFetch(`/api/logs?${params.toString()}${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs by level')
      const data = await response.json()
      logs.value[service] = data.logs || []
      logsMeta.value[service] = { total: data.total || (data.logs||[]).length, offset: data.offset ?? 0 }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logOffset.value[service] = data.offset ?? 0
      logHasMorePrev.value[service] = data.has_more_prev ?? false
      logHasMoreNext.value[service] = data.has_more_next ?? false
      await fetchLogLevelCounts(service)
      searchMatches.value[service] = []
      currentMatchIndex.value[service] = -1
      await nextTick()
      scrollLogsToBottom()
    } catch (e) {
      console.error('fetchLogsByLevel error:', e)
      showNotification(t('logs_load_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  let logSocket = null
  let logSocketService = null
  let logSocketReconnectTimer = null

  const connectLogWebSocket = (service) => {
    if (!service) return
    if (authToken && !authToken.value) return
    logSocketService = service
    if (logSocketReconnectTimer) {
      clearTimeout(logSocketReconnectTimer)
      logSocketReconnectTimer = null
    }
    if (logSocket) logSocket.close()
  const token = authToken?.value ? encodeURIComponent(authToken.value) : ''
  const wsUrl = buildWsUrl(`/api/ws/logs/${service}?token=${token}`)
    logSocket = new WebSocket(wsUrl)
    logSocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'log') {
        if (logMode.value !== 'live') return
        const meta = logsMeta.value[service]
        const offset = meta ? (meta.offset || 0) : 0
        const curLen = logs.value[service]?.length || 0
        data.line = offset + curLen + 1
        const arr = [...(logs.value[service] || []), data]
        if (arr.length > LIVE_LOG_LIMIT) arr.splice(0, arr.length - LIVE_LOG_LIMIT)
        logs.value[service] = arr
        if (logsMeta.value[service]) {
          logsMeta.value[service].total = offset + arr.length
        } else {
          logsMeta.value[service] = { total: offset + arr.length, offset }
        }
        if (followLogs.value && !logPaused.value) nextTick(scrollLogsToBottom)
      }
    }
    logSocket.onclose = () => {
      if (selectedService.value && logSocketService === selectedService.value && service === selectedService.value) {
        logSocketReconnectTimer = setTimeout(() => connectLogWebSocket(service), 2000)
      }
    }
  }

  const cleanupLogsSocket = () => {
    if (logSocketReconnectTimer) {
      clearTimeout(logSocketReconnectTimer)
      logSocketReconnectTimer = null
    }
    if (logSocket) {
      logSocket.close()
      logSocket = null
      logSocketService = null
    }
  }

  const logLevelCounts = ref({ ERROR: 0, WARNING: 0, INFO: 0, DEBUG: 0 })

  const getLogLevelCount = (level) => {
    if (logMode.value === 'history') {
      return logLevelCounts.value[level] || 0
    }
    return displayedLogs.value.filter(l => l.level === level).length
  }

  const fetchLogLevelCounts = async (service) => {
    if (!service) return
    try {
      const resp = await authorizedFetch(`/api/logs/level-counts?service=${service}`)
      if (resp.ok) {
        const data = await resp.json()
        logLevelCounts.value = data.counts || { ERROR: 0, WARNING: 0, INFO: 0, DEBUG: 0 }
      }
    } catch (e) {
      logLevelCounts.value = { ERROR: 0, WARNING: 0, INFO: 0, DEBUG: 0 }
    }
  }

  const setLogMode = (mode) => {
    if (!['live', 'history'].includes(mode)) return
    if (logMode.value === mode) return
    logMode.value = mode
    const svc = selectedService.value
    if (!svc) return
    logLevelFilter.value = 'ALL'
    _logSearchSuppressWatch = true
    logSearch.value = ''
    searchMatches.value[svc] = []
    currentMatchIndex.value[svc] = -1

    if (mode === 'live') {
      logPaused.value = false
      followLogs.value = true
      logs.value[svc] = []
      logsMeta.value[svc] = { total: 0, offset: 0 }
      connectLogWebSocket(svc)
    } else {
      if (logSocket) { logSocket.close(); logSocket = null; logSocketService = null }
      logPaused.value = false
      followLogs.value = false
      loadLogs(svc)
      fetchLogLevelCounts(svc)
    }
  }

  const displayedLogs = computed(() => {
    return logs.value[selectedService.value] || []
  })

  const filteredDisplayedLogs = computed(() => {
    const all = displayedLogs.value
    if (logLevelFilter.value === 'ALL') {
      return all.map((log, idx) => ({ ...log, _origIdx: idx, _fIdx: idx }))
    }
    const filtered = []
    all.forEach((log, idx) => {
      if (log.level === logLevelFilter.value) {
        filtered.push({ ...log, _origIdx: idx, _fIdx: filtered.length })
      }
    })
    return filtered
  })

  const totalLogs = computed(() => {
    return logs.value[selectedService.value]?.length || 0
  })

  let logSearchDebounceTimer = null
  let logSearchInProgress = false
  let _logSearchSuppressWatch = false
  watch(logSearch, (keyword) => {
    if (logSearchDebounceTimer) clearTimeout(logSearchDebounceTimer)
    if (!keyword) {
      logSearchInProgress = false
      const service = selectedService.value
      if (!service) return
      searchMatches.value[service] = []
      currentMatchIndex.value[service] = -1
      if (_logSearchSuppressWatch) {
        _logSearchSuppressWatch = false
        return
      }
      if (logMode.value === 'history') {
        const lvl = logLevelFilter.value
        if (lvl && lvl !== 'ALL') {
          fetchLogsByLevel(lvl)
        } else {
          logsLoading.value[service] = true
          authorizedFetch(`/api/logs?service=${service}&lines=200&offset=-200${toRangeQuery()}`)
            .then(async response => {
              if (response.ok) {
                const data = await response.json()
                logs.value[service] = data.logs
                logsMeta.value[service] = { total: data.total, offset: data.offset }
                if (data.log_size != null) logFileSize.value[service] = data.log_size
                logOffset.value[service] = data.offset
                logHasMorePrev.value[service] = data.has_more_prev
                logHasMoreNext.value[service] = data.has_more_next
                await nextTick()
                scrollLogsToBottom()
              }
            })
            .catch(() => {})
            .finally(() => { logsLoading.value[service] = false })
        }
      } else {
        followLogs.value = true
        nextTick(() => scrollLogsToBottom())
      }
      return
    }
    logSearchDebounceTimer = setTimeout(async () => {
      const service = selectedService.value
      if (!service) return
      if (logMode.value === 'history') {
        if (logSearchInProgress) return
        logSearchInProgress = true
        try {
          const params = new URLSearchParams({ service, search: keyword })
          if (logLevelFilter.value && logLevelFilter.value !== 'ALL') {
            params.set('level', logLevelFilter.value)
          }
          const rangeQ = toRangeQuery()
          const response = await authorizedFetch(`/api/logs/search-matches?${params.toString()}${rangeQ}`)
          if (!response.ok) throw new Error('Failed to search logs')
          if (logSearch.value !== keyword) return
          const data = await response.json()
          const matches = (data.matches || []).map(n => n - 1)
          searchMatches.value[service] = matches
          currentMatchIndex.value[service] = matches.length > 0 ? 0 : -1
          if (matches.length > 0) {
            await scrollToSearchMatch(service, 0)
          }
        } catch (e) {
          console.error('Search logs error:', e)
          showNotification(t('search_failed'), 'error')
        } finally {
          logSearchInProgress = false
        }
      } else {
        const matches = []
        const kw = keyword.toLowerCase()
        const list = filteredDisplayedLogs.value
        list.forEach((log) => {
          if (log.raw && log.raw.toLowerCase().includes(kw) && log.line != null) {
            matches.push(log.line)
          }
        })
        searchMatches.value[service] = matches
        currentMatchIndex.value[service] = matches.length > 0 ? 0 : -1
        if (matches.length > 0) {
          await nextTick()
          scrollToSearchMatch(service, 0)
        }
      }
    }, 500)
  })

  const goBackToLastPosition = async () => {
    const service = selectedService.value
    if (!service) return
    const last = logLastPosition.value[service]
    if (!last) return
    logsLoading.value[service] = true
    try {
      const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=${last.offset}${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      logs.value[service] = data.logs
      logsMeta.value[service] = { total: data.total, offset: data.offset }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logOffset.value[service] = data.offset
      logHasMorePrev.value[service] = data.has_more_prev
      logHasMoreNext.value[service] = data.has_more_next
      await nextTick()
      if (logsContainer.value) {
        logsContainer.value.scrollTop = last.scrollTop || 0
      }
    } catch (e) {
      console.error('Go back position error:', e)
      showNotification(t('jump_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  const rememberCurrentPosition = () => {
    const service = selectedService.value
    if (!service || !logsContainer.value) return
    logLastPosition.value[service] = {
      offset: logOffset.value[service] || 0,
      scrollTop: logsContainer.value.scrollTop || 0
    }
  }

  const scrollToLineCenter = (targetLine, smooth = true) => {
    const container = logsContainer.value
    if (!container) return
    const lineNode = container.querySelector(`[data-line="${targetLine}"]`)
    if (lineNode) {
      const containerRect = container.getBoundingClientRect()
      const lineRect = lineNode.getBoundingClientRect()
      const lineTopInScroll = lineRect.top - containerRect.top + container.scrollTop
      const targetScroll = lineTopInScroll - (container.clientHeight / 2) + (lineNode.offsetHeight / 2)
      container.scrollTo({ top: Math.max(targetScroll, 0), behavior: smooth ? 'smooth' : 'auto' })
    }
    if (highlightedLogLineTimer) clearTimeout(highlightedLogLineTimer)
    highlightedLogLine.value = targetLine
    highlightedLogLineTimer = setTimeout(() => { highlightedLogLine.value = null }, 2500)
  }

  const jumpToLogLine = async (globalIndex) => {
    const service = selectedService.value
    if (!service) return
    if (logMode.value === 'history') {
      logLevelFilter.value = 'ALL'
      _logSearchSuppressWatch = true
      logSearch.value = ''
    }
    const pageSize = 200
    const pageOffset = Math.floor(globalIndex / pageSize) * pageSize
    logsLoading.value[service] = true
    try {
      const response = await authorizedFetch(`/api/logs?service=${service}&lines=${pageSize}&offset=${pageOffset}${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      logs.value[service] = data.logs
      logsMeta.value[service] = { total: data.total, offset: data.offset }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logOffset.value[service] = data.offset
      logHasMorePrev.value[service] = data.has_more_prev
      logHasMoreNext.value[service] = data.has_more_next
      logsLoading.value[service] = false
      let targetLine = globalIndex + 1
      if (Array.isArray(data.logs)) {
        const found = data.logs.find(l => typeof l.line === 'number' && (l.line - 1) === globalIndex)
        if (found) targetLine = found.line
      }
      await nextTick()
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
      scrollToLineCenter(targetLine)
    } catch (e) {
      console.error('Jump to log line error:', e)
      showNotification(t('jump_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  const jumpToNextMatch = () => {
    const service = selectedService.value
    if (!service) return
    const matches = searchMatches.value[service] || []
    if (!matches.length) return
    const current = currentMatchIndex.value[service] ?? -1
    const nextIndex = current < matches.length - 1 ? current + 1 : 0
    currentMatchIndex.value[service] = nextIndex
    scrollToSearchMatch(service, nextIndex)
  }

  const jumpToPrevMatch = () => {
    const service = selectedService.value
    if (!service) return
    const matches = searchMatches.value[service] || []
    if (!matches.length) return
    const current = currentMatchIndex.value[service] ?? 0
    const prevIndex = current > 0 ? current - 1 : matches.length - 1
    currentMatchIndex.value[service] = prevIndex
    scrollToSearchMatch(service, prevIndex)
  }

  const scrollToSearchMatch = async (service, matchArrIdx) => {
    const matches = searchMatches.value[service]
    if (!matches?.length || matchArrIdx < 0 || matchArrIdx >= matches.length) return
    const matchValue = matches[matchArrIdx]
    if (logMode.value === 'live') {
      await nextTick()
      scrollToLineCenter(matchValue)
    } else {
      const targetLine = matchValue
      const currentLogs = logs.value[service] || []
      const found = currentLogs.find(l => l.line === targetLine)
      if (found) {
        await nextTick()
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
        scrollToLineCenter(targetLine)
      } else {
        const pageSize = 200
        const pageOffset = Math.max(0, matchValue - 1 - Math.floor(pageSize / 2))
        logsLoading.value[service] = true
        try {
          const params = new URLSearchParams({ service, lines: String(pageSize), offset: String(pageOffset) })
          const rangeQ = toRangeQuery()
          const response = await authorizedFetch(`/api/logs?${params.toString()}${rangeQ}`)
          if (!response.ok) throw new Error('Failed to fetch logs')
          const data = await response.json()
          logs.value[service] = data.logs
          logsMeta.value[service] = { total: data.total, offset: data.offset }
          if (data.log_size != null) logFileSize.value[service] = data.log_size
          logOffset.value[service] = data.offset
          logHasMorePrev.value[service] = data.has_more_prev
          logHasMoreNext.value[service] = data.has_more_next
          logsLoading.value[service] = false
          await nextTick()
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
          scrollToLineCenter(targetLine)
        } catch (e) {
          console.error('Search match jump error:', e)
        } finally {
          logsLoading.value[service] = false
        }
      }
    }
  }

  const loadLogs = async (service) => {
    selectedService.value = service
    _logSearchSuppressWatch = true
    logSearch.value = ''
    logsLoading.value[service] = true
    logs.value[service] = []
    logOffset.value[service] = 0
    logHasMorePrev.value[service] = false
    logHasMoreNext.value[service] = false

    if (logMode.value === 'live') {
      logPaused.value = false
      followLogs.value = true
      logsMeta.value[service] = { total: 0, offset: 0 }
      logsLoading.value[service] = false
      return
    }

    try {
      if (logLevelFilter.value && logLevelFilter.value !== 'ALL') {
        await fetchLogsByLevel(logLevelFilter.value)
        return
      }
      const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=-200${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      logs.value[service] = data.logs
      logsMeta.value[service] = { total: data.total, offset: data.offset }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logOffset.value[service] = data.offset
      logHasMorePrev.value[service] = data.has_more_prev
      logHasMoreNext.value[service] = data.has_more_next
      await nextTick()
      await nextTick()
      scrollLogsToBottom()
    } catch (error) {
      console.error('Error loading logs:', error)
      showNotification(t('logs_load_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  const toRangeQuery = () => {
    return (logMode.value === 'history' && logTimeRange.value && logTimeRange.value !== 'all')
      ? `&range=${encodeURIComponent(logTimeRange.value)}`
      : ''
  }

  const fetchMoreLogs = async (direction = 'prev') => {
    const service = selectedService.value
    if (!service) return
    if (logsLoading.value[service]) return
    logsLoading.value[service] = true
    const currentLogs = logs.value[service] || []
    const offset = logOffset.value[service] || 0
    let fetchOffset, scrollTo
    if (direction === 'prev' && logHasMorePrev.value[service]) {
      fetchOffset = Math.max(offset - 200, 0)
      scrollTo = 'top'
    } else if (direction === 'next' && logHasMoreNext.value[service]) {
      fetchOffset = offset + currentLogs.length
      scrollTo = 'bottom'
    } else {
      logsLoading.value[service] = false
      return
    }
    try {
      const lvl = logLevelFilter.value && logLevelFilter.value !== 'ALL' ? `&level=${encodeURIComponent(logLevelFilter.value)}` : ''
      const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=${fetchOffset}${lvl}${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      if (direction === 'prev') {
        logs.value[service] = data.logs.concat(currentLogs)
        logOffset.value[service] = data.offset
      } else {
        logs.value[service] = currentLogs.concat(data.logs)
      }
      logsMeta.value[service] = { total: data.total, offset: data.offset }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logHasMorePrev.value[service] = data.has_more_prev
      logHasMoreNext.value[service] = data.has_more_next
      await nextTick()
      if (scrollTo === 'top') scrollLogsToTop()
      if (scrollTo === 'bottom') scrollLogsToBottom()
    } catch (error) {
      showNotification(t('logs_load_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  const togglePause = async () => {
    if (logMode.value !== 'live') return
    logPaused.value = !logPaused.value
    if (logSocket && logSocket.readyState === 1) {
      logSocket.send(JSON.stringify({ action: logPaused.value ? 'pause' : 'resume' }))
    }
    if (logPaused.value) {
      followLogs.value = false
    } else {
      followLogs.value = true
      await nextTick()
      scrollLogsToBottom()
    }
  }

  const downloadLogs = async () => {
    try {
      const response = await authorizedFetch(`/api/logs/download?service=${selectedService.value}`)
      if (!response.ok) throw new Error('Download failed')
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedService.value}-logs-${Date.now()}.log`
      a.click()
      window.URL.revokeObjectURL(url)
      showNotification(t('download_success'), 'success')
    } catch (error) {
      console.error('Download error:', error)
      showNotification(t('download_failed'), 'error')
    }
  }

  const clearLogs = () => {
    const service = selectedService.value
    if (!service) return
    const doClear = () => {
      logs.value[service] = []
      logsMeta.value[service] = { total: 0, offset: 0 }
      ;(async () => {
        try {
          const resp = await authorizedFetch(`/api/logs?service=${service}&lines=1&offset=-1`)
          if (resp.ok) {
            const data = await resp.json()
            logsMeta.value[service] = { total: data.total, offset: data.offset }
            if (data.log_size != null) logFileSize.value[service] = data.log_size
          }
        } catch (e) {}
      })()
      searchMatches.value[service] = []
      currentMatchIndex.value[service] = -1
      logHasMorePrev.value[service] = false
      logHasMoreNext.value[service] = false
      logLevelFilter.value = 'ALL'
      if (logSocket && logSocket.readyState === 1) {
        logSocket.send(JSON.stringify({ action: 'clear' }))
      }
      showNotification(t('clear_logs_success'), 'success')
    }
    if (openConfirmDialog) {
      openConfirmDialog({
        type: 'danger',
        title: t('clear_logs_title'),
        message: t('clear_logs_confirm'),
        confirmText: t('clear_logs_action'),
        onConfirm: doClear,
      })
      return
    }
    doClear()
  }

  const getLogColor = (level) => {
    const colors = {
      ERROR: 'text-red-400',
      WARNING: 'text-yellow-300',
      INFO: 'text-green-400',
      DEBUG: 'text-blue-400'
    }
    return colors[level] || 'text-gray-400'
  }

  const goToBottom = async () => {
    const service = selectedService.value
    if (!service) return
    if (logMode.value === 'live') {
      followLogs.value = true
      await nextTick()
      if (!logsContainer.value) return
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
      return
    }
    logsLoading.value[service] = true
    try {
      const lvl = logLevelFilter.value && logLevelFilter.value !== 'ALL' ? `&level=${encodeURIComponent(logLevelFilter.value)}` : ''
      const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=-200${lvl}${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      logs.value[service] = data.logs
      logsMeta.value[service] = { total: data.total, offset: data.offset }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logOffset.value[service] = data.offset
      logHasMorePrev.value[service] = data.has_more_prev
      logHasMoreNext.value[service] = data.has_more_next
      await nextTick()
      await nextTick()
      scrollLogsToBottom()
    } catch (e) {
      console.error('Go to bottom error:', e)
      showNotification(t('jump_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  const goToTop = async () => {
    const service = selectedService.value
    if (!service) return
    if (logMode.value === 'live') {
      followLogs.value = false
      await nextTick()
      if (!logsContainer.value) return
      logsContainer.value.scrollTop = 0
      return
    }
    logsLoading.value[service] = true
    try {
      const lvl = logLevelFilter.value && logLevelFilter.value !== 'ALL' ? `&level=${encodeURIComponent(logLevelFilter.value)}` : ''
      const response = await authorizedFetch(`/api/logs?service=${service}&lines=200&offset=0${lvl}${toRangeQuery()}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      logs.value[service] = data.logs
      logsMeta.value[service] = { total: data.total, offset: data.offset }
      if (data.log_size != null) logFileSize.value[service] = data.log_size
      logOffset.value[service] = data.offset
      logHasMorePrev.value[service] = data.has_more_prev
      logHasMoreNext.value[service] = data.has_more_next
      await nextTick()
      await nextTick()
      scrollLogsToTop()
    } catch (e) {
      console.error('Go to top error:', e)
      showNotification(t('jump_failed'), 'error')
    } finally {
      logsLoading.value[service] = false
    }
  }

  const scrollLogsToBottom = () => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
      requestAnimationFrame(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      })
    }
  }

  const scrollLogsToTop = () => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = 0
      requestAnimationFrame(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = 0
        }
      })
    }
  }

  watch(selectedService, (service) => {
    if (service && logMode.value === 'history') {
      fetchLogLevelCounts(service)
    }
    if (!service) {
      cleanupLogsSocket()
      return
    }
    if (logMode.value === 'live') {
      connectLogWebSocket(service)
    }
  }, { immediate: true })

  return {
    logs,
    logsLoading,
    logsMeta,
    logFileSize,
    logOffset,
    logHasMorePrev,
    logHasMoreNext,
    logLastPosition,
    searchMatches,
    currentMatchIndex,
    logPaused,
    followLogs,
    highlightedLogLine,
    logSearch,
    logLevelFilter,
    LIVE_LOG_LIMIT,
    logTimeRange,
    logTimeRangeOptions,
    logLevelFilters,
    logMode,
    logLevelCounts,
    getLogLevelCount,
    onLogLevelClick,
    closeLogViewer,
    isCurrentMatchLine,
    getLogLineNumber,
    onLineNumberClick,
    highlightLogText,
    onLogsScroll,
    fetchLogsByLevel,
    connectLogWebSocket,
    cleanupLogsSocket,
    setLogMode,
    displayedLogs,
    filteredDisplayedLogs,
    totalLogs,
    goBackToLastPosition,
    rememberCurrentPosition,
    scrollToLineCenter,
    jumpToLogLine,
    jumpToNextMatch,
    jumpToPrevMatch,
    scrollToSearchMatch,
    loadLogs,
    toRangeQuery,
    fetchMoreLogs,
    togglePause,
    downloadLogs,
    clearLogs,
    getLogColor,
    goToBottom,
    goToTop,
    scrollLogsToBottom,
    scrollLogsToTop,
    formatFileSize,
  }
}
