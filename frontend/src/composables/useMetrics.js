import { ref, computed, watch, nextTick } from 'vue'

let echartsModule = null
const loadEcharts = async () => {
  if (!echartsModule) {
    const mod = await import('echarts')
    echartsModule = mod
  }
  return echartsModule
}

export function useMetrics({
  authorizedFetch,
  buildApiUrl,
  showNotification,
  t,
  authToken,
  isDark,
}) {
  const metricsService = ref(null)
  const metricsHistory = ref({})
  const metricsLoading = ref(false)
  const metricsRangeHours = ref(24)
  let metricsEventSource = null
  let cpuChart = null
  let memoryChart = null
  let diskChart = null
  let metricsResizeHandler = null

  const showMetricsTrend = ref(false)
  const metricsTrendType = ref('cpu')
  const trendRange = ref('1h')
  const trendData = ref([])
  const trendLoading = ref(false)
  let trendChartInstance = null

  const trendRangeOptions = computed(() => [
    { value: '1h', label: t('range_1h') },
    { value: '6h', label: t('range_6h') },
    { value: '24h', label: t('range_24h') },
    { value: '7d', label: t('range_7d') },
    { value: '30d', label: t('range_30d') },
    { value: 'all', label: t('range_all') },
  ])

  const parseMetricsTimestamp = (timestamp) => {
    if (!timestamp) return null
    let safe = timestamp
    const [base, fractional = ''] = safe.split('.')
    const ms = fractional.replace(/Z$/i, '').slice(0, 3).padEnd(3, '0')
    safe = `${base}.${ms}Z`
    const t = Date.parse(safe)
    return Number.isNaN(t) ? null : t
  }

  const formatMetricsTime = (timestamp) => {
    const t = parseMetricsTimestamp(timestamp)
    if (!t) return ''
    const d = new Date(t)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  const initMetricsCharts = async () => {
    const echarts = await loadEcharts()
    const cpuEl = document.getElementById('metrics-cpu-chart')
    const memEl = document.getElementById('metrics-memory-chart')
    const diskEl = document.getElementById('metrics-disk-chart')
    if (cpuEl) {
      if (cpuChart) cpuChart.dispose()
      cpuChart = echarts.init(cpuEl)
    }
    if (memEl) {
      if (memoryChart) memoryChart.dispose()
      memoryChart = echarts.init(memEl)
    }
    if (diskEl) {
      if (diskChart) diskChart.dispose()
      diskChart = echarts.init(diskEl)
    }

    metricsResizeHandler = () => {
      cpuChart?.resize()
      memoryChart?.resize()
      diskChart?.resize()
    }
    window.addEventListener('resize', metricsResizeHandler)
  }

  const ensureMetricsCharts = async () => {
    const echarts = await loadEcharts()
    const cpuEl = document.getElementById('metrics-cpu-chart')
    const memEl = document.getElementById('metrics-memory-chart')
    const diskEl = document.getElementById('metrics-disk-chart')
    if (!cpuChart && cpuEl) {
      cpuChart = echarts.init(cpuEl)
    }
    if (!memoryChart && memEl) {
      memoryChart = echarts.init(memEl)
    }
    if (!diskChart && diskEl) {
      diskChart = echarts.init(diskEl)
    }
  }

  const getMetricsPoints = (service) => {
    const points = metricsHistory.value[service] || []
    if (!metricsRangeHours.value || metricsRangeHours.value >= 24) return points
    const cutoff = Date.now() - metricsRangeHours.value * 3600 * 1000
    return points.filter(p => {
      const t = parseMetricsTimestamp(p.timestamp)
      return t && t >= cutoff
    })
  }

  const updateMetricsCharts = async () => {
    const service = metricsService.value
    if (!service) return
    await ensureMetricsCharts()
    const points = getMetricsPoints(service)
    if (!points || !points.length) return

    const labels = points.map(p => formatMetricsTime(p.timestamp))
    const cpuData = points.map(p => Number(p.cpu_percent ?? 0))
    const memData = points.map(p => Number(p.memory_mb ?? 0))
    const readData = points.map(p => Number(p.read_mb_s ?? 0))
    const writeData = points.map(p => Number(p.write_mb_s ?? 0))

    cpuChart?.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: labels, boundaryGap: false },
      yAxis: { type: 'value', name: '%' },
      series: [{
        name: 'CPU',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: cpuData,
        lineStyle: { color: '#2563eb', width: 2 }
      }]
    })

    memoryChart?.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 60, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: labels, boundaryGap: false },
      yAxis: { type: 'value', name: 'MB' },
      series: [{
        name: 'Memory',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: memData,
        lineStyle: { color: '#7c3aed', width: 2 }
      }]
    })

    diskChart?.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['Read', 'Write'], top: 0 },
      grid: { left: 60, right: 20, top: 30, bottom: 30 },
      xAxis: { type: 'category', data: labels, boundaryGap: false },
      yAxis: { type: 'value', name: 'MB/s' },
      series: [
        {
          name: 'Read',
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: readData,
          lineStyle: { color: '#f97316', width: 2 }
        },
        {
          name: 'Write',
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: writeData,
          lineStyle: { color: '#10b981', width: 2 }
        }
      ]
    })
  }

  const refreshMetricsHistory = async () => {
    const service = metricsService.value
    if (!service) return
    metricsLoading.value = true
    try {
      const response = await authorizedFetch(`/api/metrics/history?service=${service}`)
      if (!response.ok) throw new Error('Failed to load metrics history')
      const data = await response.json()
      metricsHistory.value[service] = data.points || []
      await nextTick()
  await updateMetricsCharts()
    } catch (e) {
      console.error('Load metrics history error:', e)
      showNotification(t('metrics_load_failed'), 'error')
    } finally {
      metricsLoading.value = false
    }
  }

  const setupMetricsSSE = (service) => {
    if (!authToken?.value) return
    if (metricsEventSource) metricsEventSource.close()
    metricsEventSource = new EventSource(
      buildApiUrl(`/api/metrics/sse?service=${service}&token=${encodeURIComponent(authToken.value || '')}`)
    )
    metricsEventSource.onmessage = (event) => {
      try {
        const point = JSON.parse(event.data)
        const history = metricsHistory.value[service] || []
        const last = history[history.length - 1]
        if (last && last.timestamp === point.timestamp) {
          history[history.length - 1] = point
        } else {
          history.push(point)
        }
        metricsHistory.value[service] = history
      } catch (e) {}
    }
  }

  const openMetrics = async (service) => {
    metricsService.value = service
    await nextTick()
    await nextTick()
    await initMetricsCharts()
    await refreshMetricsHistory()
    setupMetricsSSE(service)
    await updateMetricsCharts()
  }

  const cleanupMetricsStream = () => {
    if (metricsEventSource) {
      metricsEventSource.close()
      metricsEventSource = null
    }
  }

  const closeMetrics = () => {
    metricsService.value = null
    cleanupMetricsStream()
    if (metricsResizeHandler) {
      window.removeEventListener('resize', metricsResizeHandler)
      metricsResizeHandler = null
    }
    if (cpuChart) {
      cpuChart.dispose()
      cpuChart = null
    }
    if (memoryChart) {
      memoryChart.dispose()
      memoryChart = null
    }
    if (diskChart) {
      diskChart.dispose()
      diskChart = null
    }
  }

  const resetMetricsHistory = () => {
    metricsHistory.value = {}
  }

  const openMetricsTrend = (type) => {
    metricsTrendType.value = type
    trendRange.value = '1h'
    showMetricsTrend.value = true
    trendData.value = []
    loadMetricsTrend()
  }

  const loadMetricsTrend = async () => {
    trendLoading.value = true
    try {
      const response = await authorizedFetch(`/api/system-metrics/history?range=${trendRange.value}`)
      if (response.ok) {
        const data = await response.json()
        trendData.value = data.points || []
      }
    } catch (e) {
      console.error('Load metrics trend error:', e)
    } finally {
      trendLoading.value = false
    }
    // Wait for DOM to update after trendLoading becomes false (v-if/v-else renders chart div)
    await nextTick()
    await nextTick()
    void renderTrendChart()
  }

  const renderTrendChart = async () => {
    const trendEl = document.getElementById('trend-chart')
    if (!trendEl || !trendData.value.length) return
    if (trendChartInstance) {
      trendChartInstance.dispose()
    }
    const echarts = await loadEcharts()
    trendChartInstance = echarts.init(trendEl, isDark?.value ? 'dark' : undefined)
    const isCpu = metricsTrendType.value === 'cpu'
    const times = trendData.value.map(p => {
      const d = new Date(p.t)
      const pad = (n) => String(n).padStart(2, '0')
      if (['7d', '30d', 'all'].includes(trendRange.value)) {
        return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
      }
      return `${pad(d.getHours())}:${pad(d.getMinutes())}`
    })
    const values = trendData.value.map(p => isCpu ? p.c : p.m)
    const color = isCpu ? '#3b82f6' : '#a855f7'
    const areaColor = isCpu
      ? { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.25)' }, { offset: 1, color: 'rgba(59,130,246,0.02)' }] }
      : { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(168,85,247,0.25)' }, { offset: 1, color: 'rgba(168,85,247,0.02)' }] }
    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          const p = params[0]
          return `<div style="font-size:12px">${p.name}<br/><strong>${p.value}%</strong></div>`
        }
      },
      grid: { left: 50, right: 20, top: 20, bottom: 40 },
      xAxis: {
        type: 'category',
        data: times,
        axisLabel: { fontSize: 10, color: '#9ca3af', rotate: times.length > 100 ? 45 : 0 },
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { fontSize: 10, color: '#9ca3af', formatter: '{value}%' },
        splitLine: { lineStyle: { color: isDark?.value ? '#334155' : '#f3f4f6' } },
      },
      series: [{
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color },
        areaStyle: { color: areaColor },
      }],
      dataZoom: [{
        type: 'inside',
        start: 0,
        end: 100,
      }],
    }
    trendChartInstance.setOption(option)
  }

  watch(metricsRangeHours, () => {
    void updateMetricsCharts()
  })

  watch(showMetricsTrend, (val) => {
    if (!val && trendChartInstance) {
      trendChartInstance.dispose()
      trendChartInstance = null
    }
  })

  return {
    metricsService,
    metricsHistory,
    metricsLoading,
    metricsRangeHours,
    showMetricsTrend,
    metricsTrendType,
    trendRange,
    trendData,
    trendLoading,
    trendRangeOptions,
    openMetrics,
    closeMetrics,
    refreshMetricsHistory,
    openMetricsTrend,
    cleanupMetricsStream,
    resetMetricsHistory,
    getMetricsPoints,
  }
}
