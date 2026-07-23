<script setup lang="ts">
/**
 * 知识图谱页 -- 节点图、案例、证据
 * 基于设计稿重构
 */
import { ref, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { KnowledgeGraphResult } from '../types'
import { fetchKnowledge } from '../api'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

use([GraphChart, TooltipComponent, CanvasRenderer])

const keyword = ref('')
const graph = ref<KnowledgeGraphResult | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function doSearch() {
  if (!keyword.value.trim()) return
  loading.value = true; error.value = null
  try {
    graph.value = await fetchKnowledge({ keyword: keyword.value })
  } catch (e: any) { error.value = e.message || '查询失败' }
  finally { loading.value = false }
}

const chartOption = computed(() => {
  if (!graph.value) return {}
  const entityColors: Record<string, string> = { Equipment: '#4fa8a1', FaultSymptom: '#c96862', Component: '#c99b48', MaintenanceProcedure: '#65a984' }
  return {
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.data.name}<br/>类型: ${p.data.category}` },
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      force: { repulsion: 280, edgeLength: [140, 280] },
      label: { show: true, color: '#a3a3a3', fontSize: 11, fontFamily: 'var(--font-mono)' },
      data: graph.value.nodes.map(n => ({
        name: n.name, category: n.entity_type, symbolSize: 28,
        itemStyle: { color: entityColors[n.entity_type] || '#4fa8a1' },
      })),
      edges: graph.value.relationships.map(r => ({ source: r.start_node, target: r.end_node, label: { show: true, formatter: r.type, color: '#707070', fontSize: 9 } })),
    }],
  }
})

onMounted(() => { keyword.value = '空压机'; doSearch() })
</script>

<template>
  <div>
    <section class="page-intro">
      <div><span class="page-eyebrow">knowledge · graph explorer</span><h1 class="page-heading">知识图谱</h1></div>
      <div class="flex gap-2 items-end">
        <input v-model="keyword" placeholder="输入设备名称或症状" class="search-input" @keyup.enter="doSearch" style="width:240px" />
        <button class="primary-button" @click="doSearch">查询</button>
      </div>
    </section>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="doSearch" />

    <template v-else>
      <!-- 图谱 -->
      <section class="app-panel mb-4" v-if="graph?.nodes?.length">
        <header class="app-panel__head">
          <span class="app-panel__title">知识图谱</span>
          <span class="app-panel__code">{{ graph.nodes.length }} NODES · {{ graph.relationships?.length || 0 }} EDGES</span>
        </header>
        <div class="h-[480px] bg-[#121212]">
          <VChart :option="chartOption" autoresize style="height: 480px" />
        </div>
        <div class="p-3 border-t border-[var(--line)] flex gap-4 text-xs flex-wrap">
          <span class="flex items-center gap-1.5"><i class="w-2.5 h-2.5 rounded-full bg-[var(--cyan)] inline-block"></i>设备</span>
          <span class="flex items-center gap-1.5"><i class="w-2.5 h-2.5 rounded-full bg-[var(--red)] inline-block"></i>故障症状</span>
          <span class="flex items-center gap-1.5"><i class="w-2.5 h-2.5 rounded-full bg-[var(--amber)] inline-block"></i>部件</span>
          <span class="flex items-center gap-1.5"><i class="w-2.5 h-2.5 rounded-full bg-[var(--green)] inline-block"></i>维修步骤</span>
        </div>
      </section>
      <EmptyState v-else-if="!loading" description="暂无知识图谱数据，请输入关键词查询" />

      <!-- 历史案例 -->
      <section class="app-panel mb-4" v-if="graph?.cases?.length">
        <header class="app-panel__head"><span class="app-panel__title">历史案例</span><span class="app-panel__code">{{ graph.cases.length }} CASES</span></header>
        <el-table :data="graph.cases" size="small">
          <el-table-column label="标题" min-width="220"><template #default="{ row }"><span class="text-[var(--white)]">{{ row.title }}</span></template></el-table-column>
          <el-table-column label="相关症状" min-width="160"><template #default="{ row }">{{ row.symptom }}</template></el-table-column>
          <el-table-column label="解决方案" min-width="240" show-overflow-tooltip><template #default="{ row }">{{ row.resolution }}</template></el-table-column>
        </el-table>
      </section>

      <!-- 证据 -->
      <section class="app-panel" v-if="graph?.evidence?.length">
        <header class="app-panel__head"><span class="app-panel__title">证据来源</span><span class="app-panel__code">{{ graph.evidence.length }} EVIDENCES</span></header>
        <el-table :data="graph.evidence" size="small">
          <el-table-column prop="source_node" label="来源节点" min-width="140" />
          <el-table-column prop="target_node" label="目标节点" min-width="140" />
          <el-table-column prop="relationship" label="关系" min-width="160" />
          <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        </el-table>
      </section>
    </template>
  </div>
</template>

<style scoped>
.search-input { height:32px; min-width:200px; padding:0 10px; color:var(--white); background:#121212; border:1px solid var(--line); outline:none; font-size:13px; }
.search-input:focus { border-color:var(--cyan); box-shadow:0 0 0 2px rgba(79,168,161,.12); }
.primary-button { height:32px; padding:0 14px; border:1px solid var(--cyan); color:#d9f2ef; background:#21423f; font-size:12px; cursor:pointer; }
.primary-button:hover { background:#295550; }
</style>
