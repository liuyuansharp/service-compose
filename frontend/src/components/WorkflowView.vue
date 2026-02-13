<template>
  <div class="workflow-wrapper">
    <div class="flex items-center justify-between mb-3 gap-2">
      <div class="text-xs text-gray-500 dark:text-slate-400">
        <span v-if="!levels.length">{{ emptyLabel }}</span>
      </div>
      <div v-if="levels.length" class="flex items-center gap-1.5">
        <div class="inline-flex items-center rounded-md border border-slate-200/60 dark:border-slate-700/40 bg-white/60 dark:bg-slate-800/40 p-0.5">
          <button
            @click="viewMode = 'topo'"
            class="px-2 py-1 text-xs rounded transition"
            :class="viewMode === 'topo'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-700/40'"
          >
            {{ topoLabel }}
          </button>
          <button
            @click="viewMode = 'force'"
            class="px-2 py-1 text-xs rounded transition"
            :class="viewMode === 'force'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-slate-100/60 dark:hover:bg-slate-700/40'"
          >
            {{ forceLabel }}
          </button>
        </div>
        <button
          v-if="!isPopout"
          @click="$emit('popout')"
          class="p-1.5 rounded border border-slate-200/60 dark:border-slate-700/40 bg-white/60 dark:bg-slate-800/40 text-gray-500 dark:text-slate-300 hover:text-gray-700 dark:hover:text-slate-100 hover:bg-slate-100/60 dark:hover:bg-slate-700/40"
          :title="popoutLabel"
        >
          <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 3h7v7" /><path d="M10 14L21 3" /><path d="M21 14v7h-7" /><path d="M3 10v11h11" /></svg>
        </button>
      </div>
    </div>

    <div v-if="!levels.length" class="text-sm text-gray-500 dark:text-slate-400 py-10 text-center">
      {{ emptyLabel }}
    </div>

    <!-- Topology layout -->
    <div v-show="levels.length && viewMode === 'topo'" class="relative pb-4">
      <svg
        class="absolute inset-0 pointer-events-none"
        :width="svgWidth"
        :height="svgHeight"
        style="z-index: 0;"
      >
        <defs>
          <marker id="wf-arrow" viewBox="0 0 10 8" refX="10" refY="4" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
            <path d="M0 0 L10 4 L0 8 Z" :fill="dark ? '#64748b' : '#94a3b8'" />
          </marker>
        </defs>
        <path
          v-for="(line, li) in connectorPaths"
          :key="li"
          :d="line.d"
          fill="none"
          :stroke="dark ? '#475569' : '#cbd5e1'"
          stroke-width="1.5"
          marker-end="url(#wf-arrow)"
        />
      </svg>

      <div class="relative" style="z-index: 1;">
        <div
          v-for="(level, levelIdx) in levels"
          :key="levelIdx"
          class="flex items-start justify-center gap-3 sm:gap-4 flex-wrap"
          :class="levelIdx > 0 ? 'mt-10 sm:mt-12' : ''"
        >
          <div
            v-for="nodeName in level"
            :key="nodeName"
            :ref="el => setNodeRef(nodeName, el)"
            class="workflow-card tech-card rounded-lg p-3 transition-all min-w-[220px] max-w-[270px] flex-1"
            :class="[
              getServiceBorderClass(getServiceData(nodeName)),
              getHealthBgClass(getHealthState(getServiceData(nodeName))),
            ]"
          >
            <div class="flex justify-between items-start mb-2.5">
              <div class="min-w-0 flex-1">
                <h4 class="text-sm font-semibold text-gray-900 dark:text-slate-100 truncate">{{ nodeName }}</h4>
                <p class="text-[11px] flex items-center gap-1 mt-0.5" :class="getServiceHealthTextClass(getServiceData(nodeName))">
                  <span class="inline-block w-1.5 h-1.5 rounded-full"
                    :class="{
                      'bg-green-500 shadow-[0_0_4px_rgba(34,197,94,0.5)]': getHealthState(getServiceData(nodeName)) === 'running',
                      'bg-yellow-400 shadow-[0_0_4px_rgba(250,204,21,0.5)]': getHealthState(getServiceData(nodeName)) === 'abnormal',
                      'bg-gray-400': getHealthState(getServiceData(nodeName)) === 'stopped',
                    }"
                  ></span>
                  <span>{{ getServiceHealthLabel(getServiceData(nodeName)) }}</span>
                </p>
              </div>
              <div class="flex items-center gap-1 ml-2 flex-shrink-0">
                <button
                  v-if="getServiceData(nodeName).running && canOperate"
                  @click="$emit('control', 'stop', nodeName)"
                  class="p-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition glass-button-solid"
                  :disabled="controlling"
                  :title="stopLabel"
                >
                  <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                </button>
                <button
                  v-else-if="!getServiceData(nodeName).running && canOperate"
                  @click="$emit('control', 'start', nodeName)"
                  class="p-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition glass-button-solid"
                  :disabled="controlling"
                  :title="startLabel"
                >
                  <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8 6l10 6-10 6z" /></svg>
                </button>
                <button
                  @click="$emit('open-info', nodeName)"
                  class="p-1 bg-slate-600 text-white rounded text-xs hover:bg-slate-700 transition glass-button-solid"
                  :title="infoLabel"
                >
                  <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9" /><path d="M12 10v6" /><path d="M12 7h.01" /></svg>
                </button>
                <button
                  @click="$emit('open-metrics', nodeName)"
                  class="p-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700 transition glass-button-solid"
                  :title="metricsLabel"
                >
                  <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 18V6" /><path d="M4 18h16" /><path d="M7 14l4-4 3 3 5-6" /></svg>
                </button>
                <button
                  @click="$emit('open-logs', nodeName)"
                  class="p-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition glass-button-solid"
                  :title="logsLabel"
                >
                  <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4h7l4 4v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" /><path d="M9 12h6" /><path d="M9 16h6" /></svg>
                </button>
              </div>
            </div>

            <div class="space-y-2.5 text-[11px]">
              <div>
                <div class="flex items-center justify-between gap-2">
                  <div class="text-[10px] uppercase tracking-wider text-gray-500 dark:text-slate-400">PID</div>
                  <span class="text-[10px] text-gray-500 dark:text-slate-400 truncate">{{ uptimeLabel }}: {{ getServiceUptimeDisplay(getServiceData(nodeName)) }}</span>
                </div>
                <div class="flex items-center gap-2 mt-1">
                  <span class="font-mono text-gray-700 dark:text-slate-300">{{ getServiceData(nodeName).pid || '—' }}</span>
                  <button
                    v-if="getServiceData(nodeName).pid"
                    @click="$emit('open-pid-tree', nodeName)"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-300/40 dark:border-blue-500/30 hover:bg-blue-500/25 transition inline-flex items-center gap-0.5 whitespace-nowrap"
                    :title="pidTreeLabel"
                  >
                    <svg viewBox="0 0 24 24" class="h-2.5 w-2.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="19" r="2"/>
                      <path d="M12 7v4M12 11l-6 6M12 11l6 6"/>
                    </svg>
                    {{ pidTreeLabel }}
                  </button>
                </div>
              </div>
              <div>
                <div class="text-[10px] uppercase tracking-wider text-gray-500 dark:text-slate-400">{{ lastLogLabel }}</div>
                <p class="text-[11px] font-mono text-gray-700 dark:text-slate-300 truncate">
                  {{ getServiceData(nodeName).last_log || noLogsLabel }}
                </p>
              </div>
              <div v-if="getNodeDeps(nodeName).length" class="flex items-start gap-1 pt-0.5">
                <span class="text-gray-400 dark:text-slate-500 flex-shrink-0 mt-px">
                  <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6" /></svg>
                </span>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="dep in getNodeDeps(nodeName)"
                    :key="dep"
                    class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                    :class="isDepRunning(dep)
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'"
                  >{{ dep }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Force-directed graph -->
    <div v-show="levels.length && viewMode === 'force'" class="relative">
      <div ref="chartRef" class="workflow-force-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUpdated, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  graph: { type: Object, default: () => ({ nodes: [], edges: [] }) },
  services: { type: Array, default: () => [] },
  dark: { type: Boolean, default: false },
  isPopout: { type: Boolean, default: false },
  emptyLabel: { type: String, default: '' },
  canOperate: { type: Boolean, default: false },
  controlling: { type: Boolean, default: false },
  startLabel: { type: String, default: 'Start' },
  stopLabel: { type: String, default: 'Stop' },
  infoLabel: { type: String, default: 'Info' },
  metricsLabel: { type: String, default: 'Metrics' },
  logsLabel: { type: String, default: 'Logs' },
  uptimeLabel: { type: String, default: 'Uptime' },
  topoLabel: { type: String, default: 'Topology' },
  forceLabel: { type: String, default: 'Force' },
  popoutLabel: { type: String, default: 'Pop out' },
  pidTreeLabel: { type: String, default: 'PID Tree' },
  lastLogLabel: { type: String, default: 'Last Log' },
  noLogsLabel: { type: String, default: 'No logs yet' },
  getHealthState: { type: Function, default: () => () => 'stopped' },
  getServiceHealthLabel: { type: Function, default: () => () => '' },
  getServiceHealthTextClass: { type: Function, default: () => () => '' },
  getServiceBorderClass: { type: Function, default: () => () => '' },
  getHealthBgClass: { type: Function, default: () => () => '' },
  getServiceUptimeDisplay: { type: Function, default: () => () => '—' },
})

defineEmits(['control', 'open-info', 'open-metrics', 'open-logs', 'open-pid-tree', 'popout'])

const viewMode = ref('topo')

const serviceMap = computed(() => {
  const m = new Map()
  for (const s of props.services) {
    m.set(s.name, s)
  }
  return m
})

const getServiceData = (name) => serviceMap.value.get(name) || { name, running: false, pid: null, uptime: null, last_log: null, health: 'stopped' }

const nodeDepsMap = computed(() => {
  const m = {}
  for (const n of (props.graph?.nodes || [])) {
    m[n.id] = n.depends_on || []
  }
  return m
})
const getNodeDeps = (name) => nodeDepsMap.value[name] || []

const isDepRunning = (name) => {
  const svc = serviceMap.value.get(name)
  return svc ? props.getHealthState(svc) === 'running' : false
}

const levels = computed(() => {
  const nodes = props.graph?.nodes || []
  if (!nodes.length) return []

  const names = new Set(nodes.map(n => n.id))
  const deps = {}
  const revDeps = {}
  const inDeg = {}

  for (const n of nodes) {
    deps[n.id] = (n.depends_on || []).filter(d => names.has(d))
    revDeps[n.id] = []
    inDeg[n.id] = 0
  }
  for (const n of nodes) {
    for (const d of deps[n.id]) {
      inDeg[n.id]++
      if (revDeps[d]) revDeps[d].push(n.id)
    }
  }

  const result = []
  let ready = [...names].filter(n => inDeg[n] === 0).sort()
  let visited = 0

  while (ready.length) {
    result.push([...ready])
    const next = []
    for (const n of ready) {
      visited++
      for (const dep of (revDeps[n] || [])) {
        inDeg[dep]--
        if (inDeg[dep] === 0) next.push(dep)
      }
    }
    ready = next.sort()
  }

  if (visited < names.size) {
    const placed = new Set(result.flat())
    const rest = [...names].filter(n => !placed.has(n)).sort()
    if (rest.length) result.push(rest)
  }

  return result
})

const nodeRefs = {}
const setNodeRef = (name, el) => {
  if (el) nodeRefs[name] = el
  else delete nodeRefs[name]
}

const svgWidth = ref(0)
const svgHeight = ref(0)
const connectorPaths = ref([])

const calcConnectors = () => {
  const edges = props.graph?.edges || []
  if (!edges.length || !Object.keys(nodeRefs).length) {
    connectorPaths.value = []
    return
  }

  const wrapper = Object.values(nodeRefs)[0]?.closest('.workflow-wrapper')
  if (!wrapper) return
  const wrapperRect = wrapper.getBoundingClientRect()
  svgWidth.value = wrapper.scrollWidth
  svgHeight.value = wrapper.scrollHeight

  const paths = []
  for (const edge of edges) {
    const fromEl = nodeRefs[edge.from]
    const toEl = nodeRefs[edge.to]
    if (!fromEl || !toEl) continue

    const fromRect = fromEl.getBoundingClientRect()
    const toRect = toEl.getBoundingClientRect()

    const x1 = fromRect.left + fromRect.width / 2 - wrapperRect.left
    const y1 = fromRect.bottom - wrapperRect.top
    const x2 = toRect.left + toRect.width / 2 - wrapperRect.left
    const y2 = toRect.top - wrapperRect.top

    const midY = (y1 + y2) / 2
    paths.push({
      d: `M${x1},${y1} C${x1},${midY} ${x2},${midY} ${x2},${y2}`
    })
  }

  connectorPaths.value = paths
}

const scheduleCalc = () => {
  nextTick(() => {
    requestAnimationFrame(calcConnectors)
  })
}

onMounted(scheduleCalc)
onUpdated(scheduleCalc)

watch(() => [props.graph, props.services], scheduleCalc, { deep: true })

let _resizeObserver = null
onMounted(() => {
  nextTick(() => {
    const wrapper = document.querySelector('.workflow-wrapper')
    if (wrapper && typeof ResizeObserver !== 'undefined') {
      _resizeObserver = new ResizeObserver(scheduleCalc)
      _resizeObserver.observe(wrapper)
    }
  })
})

// ---- Force graph (ECharts) ----
const chartRef = ref(null)
let chartInstance = null

const statusColor = (state) => {
  if (state === 'running') return '#22c55e'
  if (state === 'abnormal') return '#facc15'
  return '#94a3b8'
}

const buildForceOption = () => {
  const nodes = (props.graph?.nodes || []).map(n => {
    const svc = getServiceData(n.id)
    const state = props.getHealthState(svc)
    return {
      id: n.id,
      name: n.id,
      value: svc.pid ? `PID ${svc.pid}` : 'PID —',
      symbolSize: 80,
      itemStyle: { color: statusColor(state), borderColor: props.dark ? '#0f172a' : '#f8fafc', borderWidth: 2 },
      label: {
        show: true,
        formatter: `{name|${n.id}}\n{meta|${props.getServiceHealthLabel(svc)}}`,
        rich: {
          name: { fontSize: 11, fontWeight: 600, color: props.dark ? '#e2e8f0' : '#1f2937', align: 'center', width: 120 },
          meta: { fontSize: 10, color: props.dark ? '#cbd5f5' : '#64748b', align: 'center', width: 120 },
        }
      }
    }
  })

  const edges = (props.graph?.edges || []).map(e => ({ source: e.from, target: e.to }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params) => {
        if (params.dataType === 'edge') return `${params.data.source} → ${params.data.target}`
        const svc = getServiceData(params.data.id)
        const deps = getNodeDeps(params.data.id).join(', ') || '—'
        return `<div style="font-size:12px;">${params.data.id}<br/>${props.getServiceHealthLabel(svc)}<br/>Deps: ${deps}</div>`
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: edges,
        roam: true,
        label: { position: 'inside' },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 6,
        lineStyle: { color: props.dark ? '#475569' : '#94a3b8', width: 1.2, opacity: 0.8 },
        force: { repulsion: 220, edgeLength: 120, gravity: 0.1 },
      }
    ]
  }
}

const ensureChart = () => {
  if (!chartRef.value || viewMode.value !== 'force') return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption(buildForceOption(), true)
}

const resizeChart = () => {
  if (chartInstance) chartInstance.resize()
}

watch(viewMode, () => {
  if (viewMode.value === 'force') {
    nextTick(() => {
      ensureChart()
      resizeChart()
    })
  }
})

watch(() => [props.graph, props.services, props.dark], () => {
  if (viewMode.value === 'force') {
    nextTick(() => ensureChart())
  }
}, { deep: true })

onMounted(() => {
  if (viewMode.value === 'force') {
    nextTick(() => ensureChart())
  }
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  if (_resizeObserver) _resizeObserver.disconnect()
  window.removeEventListener('resize', resizeChart)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.workflow-card {
  position: relative;
}

.workflow-force-chart {
  width: 100%;
  min-height: 520px;
  height: 60vh;
}
</style>
