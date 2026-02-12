<template>
  <div class="tech-card rounded-md p-4 sm:p-5">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-slate-100">{{ title }}</h3>
        <p class="text-xs text-gray-500 dark:text-slate-400 mt-1">{{ subtitle }}</p>
      </div>
      <button
        class="px-2.5 py-1.5 rounded-md text-xs font-medium bg-slate-700/80 text-white hover:bg-slate-700 transition"
        @click="$emit('refresh')"
      >
        {{ refreshLabel }}
      </button>
    </div>
    <div v-if="!graph?.nodes?.length" class="text-sm text-gray-500 dark:text-slate-400 py-10 text-center">
      {{ emptyLabel }}
    </div>
    <div v-else ref="chartRef" class="h-[420px] w-full"></div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  graph: { type: Object, default: () => ({ nodes: [], edges: [] }) },
  dark: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  emptyLabel: { type: String, default: '' },
  refreshLabel: { type: String, default: '' },
})

const chartRef = ref(null)
let chart = null

const buildOption = () => {
  const nodes = (props.graph?.nodes || []).map((n) => ({
    id: n.id,
    name: n.label,
    value: n.depends_on?.length || 0,
    symbolSize: 40 + Math.min((n.depends_on?.length || 0) * 6, 30),
    itemStyle: {
      color: props.dark ? '#60a5fa' : '#2563eb',
    },
    label: {
      color: props.dark ? '#e2e8f0' : '#1f2937',
      fontSize: 12,
    },
  }))

  const links = (props.graph?.edges || []).map((e) => ({
    source: e.from,
    target: e.to,
    lineStyle: {
      color: props.dark ? '#94a3b8' : '#64748b',
      width: 1.5,
    }
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params) => params.data?.name || params.data?.id
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links,
        roam: true,
        force: {
          repulsion: 240,
          edgeLength: 120,
        },
        label: { show: true },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 8,
      }
    ]
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(buildOption(), true)
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})

const handleResize = () => {
  if (chart) chart.resize()
}

watch(() => [props.graph, props.dark], () => {
  renderChart()
}, { deep: true })
</script>
