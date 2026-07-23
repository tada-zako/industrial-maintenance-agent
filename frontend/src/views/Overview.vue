<script setup lang="ts">
/**
 * 运维总览页 -- 展示设备状态、问题统计、最近草案和工作流
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DashboardSummary } from '../types'
import { fetchDashboardSummary } from '../api'
import StatusTag from '../components/StatusTag.vue'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'

use([PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const router = useRouter()
const summary = ref<DashboardSummary | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const statusPieOption = computed(() => ({
  tooltip: {
    trigger: 'item' as const,
    backgroundColor: '#1a2736',
    borderColor: '#2a3f55',
    textStyle: { color: '#e0e6ed' },
  },
  legend: {
    bottom: '0',
    textStyle: { color: '#8899aa', fontSize: 12 },
  },
  series: [{
    name: '设备状态',
    type: 'pie' as const,
    radius: ['55%', '80%'],
    center: ['50%', '50%'],
    itemStyle: { borderRadius: 4, borderColor: '#0f1923', borderWidth: 3 },
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
    data: summary.value?.device_status_distribution.map((item) => {
      const colorMap: Record<string, string> = { '正常': '#22c55e', '预警': '#eab308', '故障': '#ef4444' }
      return { ...item, itemStyle: { color: colorMap[item.name] || '#38bdf8' } }
    }) || [],
  }],
}))

const problemBarOption = computed(() => ({
  tooltip: {
    trigger: 'axis' as const,
    backgroundColor: '#1a2736',
    borderColor: '#2a3f55',
    textStyle: { color: '#e0e6ed' },
  },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category' as const,
    data: ['严重', '高', '中', '低'],
    axisLabel: { color: '#8899aa' },
    axisLine: { lineStyle: { color: '#2a3f55' } },
  },
  yAxis: {
    type: 'value' as const,
    axisLabel: { color: '#8899aa' },
    splitLine: { lineStyle: { color: '#2a3f55' } },
  },
  series: [{
    data: summary.value?.device_status_distribution
      ? [
          { value: 1, itemStyle: { color: '#dc2626' } },
          { value: 1, itemStyle: { color: '#ef4444' } },
          { value: 2, itemStyle: { color: '#eab308' } },
          { value: 1, itemStyle: { color: '#06b6d4' } },
        ]
      : [],
    type: 'bar' as const,
    barWidth: '40%',
    itemStyle: { borderRadius: [4, 4, 0, 0] },
  }],
}))

function loadSummary() {
  loading.value = true
  error.value = null
  fetchDashboardSummary()
    .then((data) => { summary.value = data })
    .catch((e) => { error.value = e.message || '加载失败' })
    .finally(() => { loading.value = false })
}

function goTo(path: string) {
  router.push(path)
}

onMounted(loadSummary)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>运维总览</h2>
      <span class="mono" style="color: var(--color-text-dim); font-size: 13px;">
        数据更新时间：{{ new Date().toLocaleString('zh-CN') }}
      </span>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadSummary" />

    <template v-else-if="summary">
      <!-- 统计卡片 -->
      <el-row :gutter="16" class="stat-cards">
        <el-col :span="6">
          <el-card shadow="never" class="stat-card" @click="goTo('/devices')">
            <div class="stat-label">设备总数</div>
            <div class="stat-value mono">{{ summary.total_devices }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-card-success" @click="goTo('/devices?status=normal')">
            <div class="stat-label">正常运行</div>
            <div class="stat-value mono" style="color: var(--color-success)">{{ summary.normal_count }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-card-warning" @click="goTo('/devices?status=warning')">
            <div class="stat-label">预警设备</div>
            <div class="stat-value mono" style="color: var(--color-warning)">{{ summary.warning_count }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-card-danger" @click="goTo('/devices?status=fault')">
            <div class="stat-label">故障设备</div>
            <div class="stat-value mono" style="color: var(--color-danger)">{{ summary.fault_count }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-label">待处理问题</div>
            <div class="stat-value mono" style="color: var(--color-warning)">{{ summary.pending_problems }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><span>设备状态分布</span></template>
            <VChart :option="statusPieOption" style="height: 260px;" autoresize />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><span>问题严重程度统计</span></template>
            <VChart :option="problemBarOption" style="height: 260px;" autoresize />
          </el-card>
        </el-col>
      </el-row>

      <!-- 最近维修草案 -->
      <el-card shadow="never" style="margin-top: 16px;">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>最近维修草案</span>
            <el-button text type="primary" size="small" @click="goTo('/drafts')">查看全部</el-button>
          </div>
        </template>
        <el-table :data="summary.recent_drafts" stripe size="small" v-if="summary.recent_drafts.length">
          <el-table-column prop="id" label="草案编号" width="110">
            <template #default="{ row }"><span class="mono">{{ row.id }}</span></template>
          </el-table-column>
          <el-table-column prop="device_name" label="设备" width="120" />
          <el-table-column prop="fault_diagnosis" label="故障判断" min-width="200" show-overflow-tooltip />
          <el-table-column label="风险等级" width="90">
            <template #default="{ row }"><SeverityTag :severity="row.risk_level" /></template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'pending_review'" type="warning" size="small">待确认</el-tag>
              <el-tag v-else-if="row.status === 'confirmed'" type="success" size="small">已确认</el-tag>
              <el-tag v-else type="info" size="small">已归档</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="goTo(`/drafts/${row.id}`)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无维修草案" />
      </el-card>

      <!-- 最近工作流 -->
      <el-card v-if="summary.latest_workflow" shadow="never" style="margin-top: 16px;">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>最近 Agent 工作流</span>
            <el-button text type="primary" size="small" @click="goTo(`/workflows/${summary.latest_workflow.id}`)">
              查看详情
            </el-button>
          </div>
        </template>
        <div class="workflow-summary">
          <div class="wf-row">
            <span class="wf-label">运行 ID：</span>
            <span class="mono" style="color: var(--color-accent)">{{ summary.latest_workflow.id }}</span>
          </div>
          <div class="wf-row">
            <span class="wf-label">用户问题：</span>
            <span style="color: var(--color-text-secondary)">{{ summary.latest_workflow.user_question }}</span>
          </div>
          <div class="wf-row">
            <span class="wf-label">目标设备：</span>
            <span>{{ summary.latest_workflow.device_name }}</span>
          </div>
          <div class="wf-row">
            <span class="wf-label">步骤数：</span>
            <span class="mono">{{ summary.latest_workflow.steps.length }}</span>
            <span class="wf-label" style="margin-left: 24px;">状态：</span>
            <el-tag v-if="summary.latest_workflow.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="summary.latest_workflow.status === 'running'" type="warning" size="small">运行中</el-tag>
            <el-tag v-else type="danger" size="small">失败</el-tag>
          </div>
        </div>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.stat-cards .stat-card {
  cursor: pointer;
  min-height: 132px;
  border-top: 2px solid var(--ui-border);
  transition: background .16s ease, border-color .16s ease;
}
.stat-cards .stat-card:hover {
  background: var(--ui-panel-raised);
}
.stat-card-success { border-top-color: var(--ui-success); }
.stat-card-warning { border-top-color: var(--ui-warning); }
.stat-card-danger { border-top-color: var(--ui-danger); }

.stat-label {
  font: 11px var(--font-mono);
  color: var(--ui-text-muted);
  letter-spacing: .04em;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--ui-text);
}

.workflow-summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
}

.wf-row {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.wf-label {
  color: var(--ui-text-quiet);
  min-width: 80px;
  flex-shrink: 0;
}

:deep(.el-card__header) { padding: 13px 16px; border-bottom-color: var(--ui-border); font-size: 13px; font-weight: 600; }
:deep(.el-card__body) { padding: 16px; }
:deep(.el-row + .el-row) { margin-top: 18px !important; }

@media (max-width: 760px) {
  :deep(.el-col) { margin-bottom: 10px; }
  .wf-row { align-items: flex-start; }
}
</style>
