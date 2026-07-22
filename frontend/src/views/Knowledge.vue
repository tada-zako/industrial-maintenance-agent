<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import { fetchKnowledge } from '../api'
import type { KnowledgeGraphResult, KnowledgeNode } from '../types'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

// 知识图谱使用 ECharts 按需构建，必须显式注册图谱、提示框和 Canvas 渲染器。
use([GraphChart, TooltipComponent, CanvasRenderer])

const route = useRoute()
const keyword = ref(String(route.query.keyword || ''))
const deviceModel = ref(String(route.query.model || ''))
const result = ref<KnowledgeGraphResult | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const selectedNode = ref<KnowledgeNode | null>(null)

const categoryColors: Record<string, string> = {
  Device: '#38bdf8',
  DeviceModel: '#06b6d4',
  Component: '#22c55e',
  FaultSymptom: '#eab308',
  FaultCause: '#ef4444',
  MaintenanceAction: '#a3e635',
  MaintenanceCase: '#f59e0b',
  SOP: '#818cf8',
  SafetyNotice: '#fb7185',
}

const graphOption = computed<EChartsOption>(() => {
  const graph = result.value
  return {
    backgroundColor: 'transparent',
    tooltip: { formatter: (params: any) => params.data?.name || params.data?.type || '' },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: { repulsion: 550, edgeLength: [80, 160], gravity: 0.08 },
      label: { show: true, color: '#e0e6ed', fontSize: 12, position: 'right' },
      edgeLabel: { show: true, color: '#8899aa', fontSize: 10, formatter: (params: any) => params.data.name },
      lineStyle: { color: '#5a6d7e', curveness: 0.1 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
      data: (graph?.nodes ?? []).map((node) => ({
        id: node.id,
        name: node.name,
        type: node.type,
        symbolSize: node.type === 'FaultCause' ? 48 : 38,
        itemStyle: { color: categoryColors[node.type] || '#8899aa' },
      })),
      links: (graph?.relationships ?? []).map((edge) => ({
        source: edge.source_id,
        target: edge.target_id,
        name: edge.type,
      })),
    }],
  }
})

async function loadKnowledge() {
  loading.value = true
  error.value = null
  selectedNode.value = null
  try {
    result.value = await fetchKnowledge({ keyword: keyword.value, deviceModel: deviceModel.value })
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '知识图谱服务暂不可用'
    result.value = null
  } finally {
    loading.value = false
  }
}

function handleChartClick(params: { data?: unknown }) {
  const nodeId = params.data && typeof params.data === 'object' && 'id' in params.data
    && typeof params.data.id === 'string'
    ? params.data.id
    : undefined
  selectedNode.value = result.value?.nodes.find((node) => node.id === nodeId) ?? null
}

function submitSearch() {
  if (!keyword.value.trim() && !deviceModel.value.trim()) {
    ElMessage.warning('请输入设备型号或故障关键词')
    return
  }
  void loadKnowledge()
}

watch(
  () => [route.query.keyword, route.query.model],
  ([nextKeyword, nextModel]) => {
    keyword.value = String(nextKeyword || '')
    deviceModel.value = String(nextModel || '')
    void loadKnowledge()
  },
)

onMounted(loadKnowledge)
</script>

<template>
  <div class="page-container knowledge-page">
    <div class="page-header">
      <div>
        <h2>知识图谱</h2>
      </div>
    </div>

    <el-card shadow="never" class="knowledge-filter">
      <el-form inline @submit.prevent="submitSearch">
        <el-form-item label="设备型号">
          <el-input v-model="deviceModel" clearable placeholder="例如 AC-SCREW-75" @keyup.enter="submitSearch" />
        </el-form-item>
        <el-form-item label="故障关键词">
          <el-input v-model="keyword" clearable placeholder="例如 温度过高" @keyup.enter="submitSearch" />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="submitSearch">查询</el-button>
      </el-form>
    </el-card>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadKnowledge" />
    <EmptyState v-else-if="result && !result.nodes.length" title="未找到关联知识" />

    <template v-else-if="result">
      <div class="knowledge-grid">
        <el-card shadow="never" class="graph-card">
          <template #header>
            <div class="card-title-row">
              <span>节点关系</span>
              <span class="mono graph-count">{{ result.nodes.length }} 节点 / {{ result.relationships.length }} 关系</span>
            </div>
          </template>
          <VChart :option="graphOption" autoresize class="graph-canvas" @click="handleChartClick" />
        </el-card>

        <el-card shadow="never" class="node-card">
          <template #header><span>节点详情</span></template>
          <el-descriptions v-if="selectedNode" :column="1" border size="small">
            <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
            <el-descriptions-item label="类型"><span class="mono">{{ selectedNode.type }}</span></el-descriptions-item>
            <el-descriptions-item label="来源">{{ selectedNode.source }}</el-descriptions-item>
            <el-descriptions-item v-if="Object.keys(selectedNode.properties).length" label="属性">
              <span class="mono">{{ JSON.stringify(selectedNode.properties) }}</span>
            </el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="请选择图谱节点" :image-size="64" />
        </el-card>
      </div>

      <el-row :gutter="16" class="knowledge-details">
        <el-col :xs="24" :lg="14">
          <el-card shadow="never">
            <template #header><span>故障诊断证据</span></template>
            <el-collapse v-if="result.matches.length">
              <el-collapse-item v-for="match in result.matches" :key="match.symptom" :title="match.symptom">
                <el-descriptions :column="1" size="small">
                  <el-descriptions-item label="可能原因">{{ match.causes.join('、') || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="维修动作">{{ match.actions.join('、') || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="SOP">{{ match.sops.join('、') || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="安全要求">{{ match.safety_notices.join('、') || '-' }}</el-descriptions-item>
                </el-descriptions>
              </el-collapse-item>
            </el-collapse>
            <el-empty v-else description="没有匹配的故障证据" :image-size="56" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="10">
          <el-card shadow="never">
            <template #header><span>历史案例</span></template>
            <el-table v-if="result.cases.length" :data="result.cases" size="small" stripe>
              <el-table-column prop="name" label="案例" min-width="140" />
              <el-table-column prop="device_model" label="型号" min-width="120" />
              <el-table-column label="关联现象" min-width="140">
                <template #default="{ row }">{{ row.symptoms.join('、') }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="没有匹配案例" :image-size="56" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="knowledge-evidence">
        <template #header><span>证据来源</span></template>
        <el-table v-if="result.evidence.length" :data="result.evidence" size="small" stripe>
          <el-table-column prop="title" label="证据" min-width="180" />
          <el-table-column prop="source_type" label="来源" width="150" />
          <el-table-column prop="reference" label="关系路径" min-width="260" />
          <el-table-column label="置信度" width="100">
            <template #default="{ row }">{{ row.confidence == null ? '-' : `${Math.round(row.confidence * 100)}%` }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="没有可展示的证据来源" :image-size="56" />
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.knowledge-filter { margin-bottom: 16px; }
.knowledge-grid { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 16px; }
.graph-card, .node-card { min-height: 520px; }
.graph-canvas { height: 450px; width: 100%; }
.card-title-row { display: flex; align-items: center; justify-content: space-between; }
.graph-count { color: var(--color-text-secondary); font-size: 12px; }
.knowledge-details { margin-top: 16px; }
.knowledge-evidence { margin-top: 16px; }
@media (max-width: 900px) {
  .knowledge-grid { grid-template-columns: 1fr; }
  .graph-card, .node-card { min-height: auto; }
  .graph-canvas { height: 380px; }
}
</style>
