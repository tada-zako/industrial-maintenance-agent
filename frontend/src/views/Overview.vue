<script setup lang="ts">
/**
 * 运维总览 -- 指标条 + 趋势图 + 关注列表 + 设备台账 + 工作流摘要
 * 基于设计稿 design-prototype.html 重构
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart, BarChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DashboardSummary, Device, MaintenanceDraft, WorkflowRun } from '../types'
import { fetchDashboardSummary, fetchDevices, fetchDrafts, fetchWorkflowDetail } from '../api'
import StatusTag from '../components/StatusTag.vue'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'

use([PieChart, BarChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const router = useRouter()

const summary = ref<DashboardSummary | null>(null)
const recentDrafts = ref<MaintenanceDraft[]>([])
const recentWorkflow = ref<WorkflowRun | null>(null)
const devices = ref<Device[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function loadAll() {
  loading.value = true
  error.value = null
  try {
    const [s, ds, ws, dvs] = await Promise.all([
      fetchDashboardSummary(),
      fetchDrafts({ page: 1, page_size: 3 }),
      fetchWorkflowDetail('latest').catch(() => null),
      fetchDevices({ page: 1, page_size: 6 }),
    ])
    summary.value = s
    recentDrafts.value = ds.items
    recentWorkflow.value = ws
    devices.value = dvs.items
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

/** 设备状态饼图 */
const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#a3a3a3', fontSize: 11 } },
  series: [{
    type: 'pie', radius: ['55%', '78%'], center: ['50%', '48%'],
    label: { show: false },
    emphasis: { label: { show: true, color: '#f2f2f0' } },
    data: [
      { value: summary.value?.normal_count ?? 0, name: '正常', itemStyle: { color: '#65a984' } },
      { value: summary.value?.warning_count ?? 0, name: '预警', itemStyle: { color: '#c99b48' } },
      { value: summary.value?.fault_count ?? 0, name: '故障', itemStyle: { color: '#c96862' } },
    ],
  }],
}))

/** 问题严重度柱状图 */
const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 0, right: 0, top: 10, bottom: 0, containLabel: true },
  xAxis: {
    type: 'category',
    data: ['严重', '高', '中', '低'],
    axisLine: { lineStyle: { color: '#303030' } },
    axisTick: { show: false },
    axisLabel: { color: '#a3a3a3', fontSize: 10, fontFamily: 'var(--font-mono)' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#303030' } },
    axisLabel: { color: '#707070', fontSize: 10, fontFamily: 'var(--font-mono)' },
  },
  series: [{
    type: 'bar',
    barWidth: 20,
    itemStyle: { borderRadius: [2, 2, 0, 0], color: '#4fa8a1' },
    emphasis: { itemStyle: { color: '#80c7c1' } },
    data: [
      summary.value?.critical_problems ?? 0,
      summary.value?.high_problems ?? 0,
      summary.value?.medium_problems ?? 0,
      summary.value?.low_problems ?? 0,
    ],
  }],
}))

function goToDevice(id: string) { router.push(`/devices/${id}`) }
function goToDraft(id: string) { router.push(`/drafts/${id}`) }
function goToWorkflow(id: string) { router.push(`/workflows/${id}`) }
</script>

<template>
  <div>
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadAll" />
    <template v-else>
      <!-- 页面头部 -->
      <section class="page-intro">
        <div>
          <span class="page-eyebrow">overview · production line a</span>
          <h1 class="page-heading">空压站运行概览</h1>
        </div>
        <div class="page-updated">2026-07-22 10:32 · 数据已刷新</div>
      </section>

      <!-- 指标条 -->
      <section class="metrics" aria-label="设备状态统计" v-if="summary">
        <article class="metric"><i class="metric-state cyan"></i><div class="metric-label">受管设备</div><div class="metric-value mono">{{ summary.total_devices }}</div><div class="metric-note">空压机与附属设备</div></article>
        <article class="metric"><i class="metric-state green"></i><div class="metric-label">正常运行</div><div class="metric-value value-green mono">{{ summary.normal_count }}</div><div class="metric-note">占总设备 {{ summary.total_devices ? Math.round(summary.normal_count / summary.total_devices * 100) : 0 }}%</div></article>
        <article class="metric"><i class="metric-state amber"></i><div class="metric-label">预警设备</div><div class="metric-value value-amber mono">{{ summary.warning_count }}</div><div class="metric-note">需要持续观察</div></article>
        <article class="metric"><i class="metric-state red"></i><div class="metric-label">故障设备</div><div class="metric-value value-red mono">{{ summary.fault_count }}</div><div class="metric-note">等待人工确认</div></article>
        <article class="metric"><i class="metric-state"></i><div class="metric-label">待处理问题</div><div class="metric-value mono">{{ summary.pending_problems }}</div><div class="metric-note">含 {{ summary.high_problems ?? 0 }} 项高优先级</div></article>
      </section>

      <!-- 图表 + 关注列表 -->
      <div class="dashboard-grid">
        <!-- 左侧：趋势 + 设备台账 -->
        <div class="flex flex-col gap-4">
          <!-- 设备状态图表 -->
          <section class="app-panel" v-if="summary">
            <header class="app-panel__head">
              <span class="app-panel__title">设备状态与问题分布</span>
              <span class="app-panel__code">DISTRIBUTION</span>
            </header>
            <div class="charts-row">
              <div class="chart-box">
                <VChart :option="pieOption" autoresize style="height: 220px" />
              </div>
              <div class="chart-box">
                <VChart :option="barOption" autoresize style="height: 220px" />
              </div>
            </div>
          </section>

          <!-- 设备运行台账 -->
          <section class="app-panel">
            <header class="app-panel__head">
              <span class="app-panel__title">设备运行台账</span>
              <button class="app-link" @click="router.push('/devices')">查看全部 →</button>
            </header>
            <div class="table-wrap">
              <table class="native-table" v-if="devices.length">
                <thead>
                  <tr>
                    <th>设备编号</th><th>设备名称</th><th>所属区域</th><th>运行状态</th>
                    <th>排气压力</th><th>温度</th><th>振动</th><th>更新时间</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="d in devices" :key="d.id">
                    <td><span class="id-link" @click="goToDevice(d.id)">{{ d.id }}</span></td>
                    <td><span class="name">{{ d.name }}</span></td>
                    <td>{{ d.area }}</td>
                    <td><StatusTag :status="d.status" /></td>
                    <td><span class="metric-num">{{ d.running_indicators?.exhaust_pressure?.toFixed(2) ?? '-' }} MPa</span></td>
                    <td>
                      <span class="metric-num" :class="{
                        'value-amber': d.status === 'warning' && (d.running_indicators?.temperature ?? 0) > 85,
                        'value-red': d.status === 'fault'
                      }">
                        {{ d.running_indicators?.temperature?.toFixed(1) ?? '-' }} °C
                      </span>
                    </td>
                    <td>
                      <span class="metric-num" :class="{
                        'value-amber': d.status === 'warning',
                        'value-red': d.status === 'fault'
                      }">
                        {{ d.running_indicators?.vibration?.toFixed(1) ?? '-' }} mm/s
                      </span>
                    </td>
                    <td class="mono muted">{{ new Date(d.updated_at).toLocaleTimeString('zh-CN', { hour12: false }) }}</td>
                    <td>
                      <button class="table-action" @click="goToDevice(d.id)">详情</button>
                      <button class="table-action secondary" @click="router.push(`/devices?edit=${d.id}`)">编辑</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <!-- 右侧：关注列表 + 最近草案 + 工作流 -->
        <div class="flex flex-col gap-4">
          <!-- 需要关注 -->
          <section class="app-panel" v-if="recentDrafts.length">
            <header class="app-panel__head">
              <span class="app-panel__title">需要关注</span>
              <button class="app-link" @click="router.push('/problems')">问题中心 →</button>
            </header>
            <div class="attention">
              <div class="attention-item" v-for="(d, i) in recentDrafts" :key="d.id">
                <i class="state-bar" :class="d.risk_level === 'critical' || d.risk_level === 'high' ? 'red' : d.risk_level === 'medium' ? 'amber' : 'cyan'"></i>
                <div>
                  <div class="attention-name">{{ d.device_name }} · {{ d.fault_diagnosis }}</div>
                  <div class="attention-detail mono">{{ new Date(d.generated_at).toLocaleString('zh-CN') }}</div>
                </div>
                <SeverityTag :severity="d.risk_level" />
              </div>
            </div>
          </section>

          <!-- 最近草案 -->
          <section class="app-panel" v-if="recentDrafts.length">
            <header class="app-panel__head">
              <span class="app-panel__title">最近维修草案</span>
              <span class="app-panel__code">{{ recentDrafts.length }} DRAFTS</span>
            </header>
            <div class="attention">
              <div class="attention-item" v-for="d in recentDrafts" :key="'draft-'+d.id" style="cursor: pointer" @click="goToDraft(d.id)">
                <i class="state-bar" :class="d.status === 'confirmed' ? 'cyan' : 'amber'"></i>
                <div>
                  <div class="attention-name">{{ d.device_name }} · {{ d.fault_diagnosis }}</div>
                  <div class="attention-detail mono">{{ d.status === 'pending_review' ? '待确认' : d.status === 'confirmed' ? '已确认' : '已归档' }}</div>
                </div>
              </div>
            </div>
          </section>

          <!-- 最近工作流 -->
          <section class="app-panel" v-if="recentWorkflow">
            <header class="app-panel__head">
              <span class="app-panel__title">最近一次 Agent 处理流程</span>
              <button class="app-link" @click="goToWorkflow(recentWorkflow.id)">查看完整工作流 →</button>
            </header>
            <div class="workflow-summary">
              <div class="workflow-meta">
                <span class="page-eyebrow">WORKFLOW / COMPLETED</span>
                <div class="mono text-xs">{{ recentWorkflow.id }}</div>
                <p v-if="recentWorkflow.device_name" class="text-xs text-[var(--quiet)] mt-2">{{ recentWorkflow.device_name }}<br/>用时 {{ recentWorkflow.total_duration?.toFixed(1) ?? '—' }} 秒 · {{ recentWorkflow.steps?.length ?? 0 }} 次工具调用</p>
              </div>
              <div class="workflow-steps-inline" v-if="recentWorkflow.steps?.length">
                <div class="step-mini" v-for="(s, si) in recentWorkflow.steps.slice(0, 5)" :key="si">
                  <i class="step-dot" :class="{ dim: s.status === 'pending' }"></i>
                  <div>
                    <h4 class="text-xs">{{ s.action || s.title }}</h4>
                    <p class="text-[10px] text-[var(--quiet)] mono" :class="{ '!text-[var(--cyan-light)]': s.status === 'completed' }">
                      {{ s.status === 'completed' ? '已完成' : s.status === 'failed' ? '失败' : '等待中' }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* 指标条 */
.metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  border: 1px solid var(--line);
  margin-bottom: 16px;
}

.metric {
  min-width: 0;
  padding: 17px 18px 18px;
  border-right: 1px solid var(--line);
  background: var(--panel);
  position: relative;
}

.metric:last-child { border-right: 0; }

.metric:hover { background: var(--panel-raised); }

.metric-label { color: var(--muted); font-size: 12px; }
.metric-value { margin-top: 4px; font: 600 29px/1.2 var(--font-mono); letter-spacing: -0.04em; }
.metric-note { margin-top: 8px; color: var(--quiet); font-size: 11px; }

.metric-state {
  position: absolute;
  right: 18px;
  top: 19px;
  width: 7px;
  height: 7px;
  background: var(--line-strong);
}

.metric-state.cyan { background: var(--cyan); }
.metric-state.green { background: var(--green); }
.metric-state.amber { background: var(--amber); }
.metric-state.red { background: var(--red); }

.value-green { color: var(--green); }
.value-amber { color: var(--amber); }
.value-red { color: var(--red); }

/* 仪表盘双栏 */
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(320px, .88fr);
  gap: 16px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 12px 18px;
  gap: 16px;
}

.chart-box {
  min-height: 220px;
  min-width: 0;
}

/* 关注列表 */
.attention { padding: 4px 18px 10px; }

.attention-item {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) auto;
  gap: 11px;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}

.attention-item:last-child { border-bottom: 0; }

.state-bar {
  width: 3px;
  height: 28px;
  background: var(--line-strong);
}

.state-bar.amber { background: var(--amber); }
.state-bar.red { background: var(--red); }
.state-bar.cyan { background: var(--cyan); }

.attention-name { font-size: 13px; color: var(--white); }

.attention-detail {
  color: var(--quiet);
  font-size: 11px;
  margin-top: 2px;
}

/* 原生表格 */
.table-wrap { overflow-x: auto; }

.native-table {
  border-collapse: collapse;
  width: 100%;
  min-width: 840px;
  text-align: left;
}

.native-table th {
  height: 39px;
  padding: 0 18px;
  color: var(--quiet);
  background: #181818;
  font: 10px var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.native-table td {
  height: 52px;
  padding: 0 18px;
  border-top: 1px solid #2a2a2a;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
}

.native-table tr:hover td { background: #202020; }

.id-link {
  color: var(--cyan-light);
  font-family: var(--font-mono);
  cursor: pointer;
}

.id-link:hover { color: var(--white); }

.name { color: var(--white); font-weight: 500; }

.metric-num { color: var(--white); font-family: var(--font-mono); }

.table-action {
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--cyan-light);
  font-size: 12px;
  cursor: pointer;
}

.table-action.secondary {
  color: var(--muted);
  margin-left: 13px;
}

.table-action:hover { color: var(--white); }

/* 工作流摘要 */
.workflow-summary {
  display: grid;
  grid-template-columns: 166px 1fr;
  min-height: 170px;
}

.workflow-meta {
  padding: 17px 18px;
  border-right: 1px solid var(--line);
}

.workflow-steps-inline {
  position: relative;
  display: flex;
  align-items: stretch;
  padding: 18px 20px;
  gap: 0;
  overflow-x: auto;
}

.workflow-steps-inline::before {
  content: '';
  height: 1px;
  background: var(--line-strong);
  position: absolute;
  top: 42px;
  left: 46px;
  right: 48px;
}

.step-mini {
  width: 22%;
  min-width: 110px;
  position: relative;
  padding: 38px 12px 0 0;
}

.step-mini:first-child { padding-left: 0; }

.step-dot {
  position: absolute;
  top: 18px;
  left: 0;
  width: 11px;
  height: 11px;
  background: var(--panel);
  border: 2px solid var(--cyan);
  border-radius: 50%;
}

.step-dot.dim { border-color: var(--line-strong); }

.step-mini h4 {
  margin: 0;
  color: var(--white);
  font-size: 12px;
  font-weight: 500;
}

.step-mini p { margin: 4px 0 0; }

/* 响应式 */
@media (max-width: 1080px) {
  .metrics { grid-template-columns: repeat(3, 1fr); }
  .metric:nth-child(3) { border-right: 0; }
  .metric:nth-child(n+4) { border-top: 1px solid var(--line); }
  .dashboard-grid { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr; }
}

@media (max-width: 760px) {
  .metrics { grid-template-columns: repeat(2, 1fr); }
  .metric { border-top: 1px solid var(--line); }
  .metric:nth-child(1), .metric:nth-child(2) { border-top: 0; }
  .metric:nth-child(even) { border-right: 0; }
  .workflow-summary { grid-template-columns: 1fr; }
  .workflow-meta { border-right: 0; border-bottom: 1px solid var(--line); }
}
</style>
