<script setup lang="ts">
/**
 * 设备详情页 -- 台账式基本信息、运行指标、分组 Tabs
 * 基于设计稿重构
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { DeviceDetail } from '../types'
import { fetchDeviceDetail } from '../api'
import StatusTag from '../components/StatusTag.vue'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const deviceId = computed(() => route.params.deviceId as string)

const device = ref<DeviceDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref('indicators')
const hermesUrl = import.meta.env.VITE_HERMES_WEB_URL || 'http://127.0.0.1:9119'

async function loadDetail() {
  loading.value = true; error.value = null
  try { device.value = await fetchDeviceDetail(deviceId.value) }
  catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function openHermes() { window.open(hermesUrl, '_blank') }
function goToDraft(draftId: string) { router.push(`/drafts/${draftId}`) }
function goToKnowledge() { if (device.value) router.push({ path: '/knowledge', query: { model: device.value.model } }) }

onMounted(loadDetail)
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <section class="page-intro">
      <div>
        <span class="page-eyebrow">device · detail</span>
        <div class="flex items-center gap-3">
          <button class="app-link text-xs" @click="router.push('/devices')">← 返回列表</button>
          <h1 class="page-heading">{{ device?.name || '设备详情' }}</h1>
        </div>
      </div>
      <div class="flex gap-2">
        <button class="filter-button" @click="goToKnowledge">关联知识图谱</button>
        <button class="primary-button" @click="openHermes">在 Hermes 中询问</button>
      </div>
    </section>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDetail" />

    <template v-else-if="device">
      <!-- 基本信息 -->
      <section class="app-panel mb-4">
        <header class="app-panel__head">
          <span class="app-panel__title">基本信息</span>
          <span class="app-panel__code mono">{{ device.id }}</span>
        </header>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="设备编号">
            <span class="mono text-[var(--cyan-light)]">{{ device.id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="设备名称">
            <span class="text-[var(--white)] font-medium">{{ device.name }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态"><StatusTag :status="device.status" /></el-descriptions-item>
          <el-descriptions-item label="设备型号">{{ device.model }}</el-descriptions-item>
          <el-descriptions-item label="所属区域">{{ device.area }}</el-descriptions-item>
          <el-descriptions-item label="额定压力">
            <span class="mono">{{ device.rated_pressure }} MPa</span>
          </el-descriptions-item>
          <el-descriptions-item label="额定功率"><span class="mono">{{ device.rated_power }} kW</span></el-descriptions-item>
          <el-descriptions-item label="投用日期">{{ device.commissioned_at }}</el-descriptions-item>
          <el-descriptions-item label="最近更新">
            <span class="mono text-xs">{{ new Date(device.updated_at).toLocaleString('zh-CN') }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </section>

      <!-- Tabs -->
      <section class="app-panel">
        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="当前运行指标" name="indicators">
            <div class="p-4" v-if="device.running_indicators">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="运行状态">{{ device.running_indicators.running_status }}</el-descriptions-item>
                <el-descriptions-item label="排气压力">
                  <span class="mono metric-num" :class="{ 'value-red': device.status === 'fault' }">
                    {{ device.running_indicators.exhaust_pressure }} MPa
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="温度">
                  <span class="mono metric-num" :class="{ 'value-amber': device.status === 'warning', 'value-red': device.status === 'fault' }">
                    {{ device.running_indicators.temperature }} °C
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="振动">
                  <span class="mono metric-num" :class="{ 'value-amber': device.status === 'warning', 'value-red': device.status === 'fault' }">
                    {{ device.running_indicators.vibration }} mm/s
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="油位">{{ device.running_indicators.oil_level }}</el-descriptions-item>
                <el-descriptions-item label="数据来源">{{ device.running_indicators.source }}</el-descriptions-item>
                <el-descriptions-item label="采集时间" :span="2">
                  <span class="mono text-xs">{{ new Date(device.running_indicators.collected_at).toLocaleString('zh-CN') }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </div>
            <EmptyState v-else description="暂无运行指标数据" />
          </el-tab-pane>

          <el-tab-pane label="历史状态记录" name="history">
            <el-table v-if="device.status_history.length" :data="device.status_history" stripe size="small" class="tab-table">
              <el-table-column label="采集时间" min-width="170">
                <template #default="{ row }"><span class="mono text-xs">{{ new Date(row.collected_at).toLocaleString('zh-CN') }}</span></template>
              </el-table-column>
              <el-table-column prop="running_status" label="运行状态" min-width="100" />
              <el-table-column label="排气压力" min-width="110"><template #default="{ row }"><span class="mono">{{ row.exhaust_pressure }} MPa</span></template></el-table-column>
              <el-table-column label="温度" min-width="90"><template #default="{ row }"><span class="mono">{{ row.temperature }}°C</span></template></el-table-column>
              <el-table-column label="振动" min-width="90"><template #default="{ row }"><span class="mono">{{ row.vibration }}mm/s</span></template></el-table-column>
              <el-table-column prop="oil_level" label="油位" min-width="80" />
              <el-table-column prop="source" label="来源" min-width="100" />
            </el-table>
            <EmptyState v-else description="暂无历史状态记录" />
          </el-tab-pane>

          <el-tab-pane label="历史故障" name="faults">
            <el-table v-if="device.historical_faults.length" :data="device.historical_faults" stripe size="small" class="tab-table">
              <el-table-column prop="symptom" label="故障现象" min-width="180" />
              <el-table-column label="严重程度" min-width="100"><template #default="{ row }"><SeverityTag :severity="row.severity" /></template></el-table-column>
              <el-table-column label="发现时间" min-width="130"><template #default="{ row }"><span class="mono text-xs">{{ row.discovered_at?.split('T')[0] ?? row.discovered_at }}</span></template></el-table-column>
              <el-table-column label="状态" min-width="100">
                <template #default="{ row }">
                  <el-tag v-if="row.status === 'resolved'" type="success" size="small">已解决</el-tag>
                  <el-tag v-else-if="row.status === 'repairing'" type="warning" size="small">维修中</el-tag>
                  <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
            </el-table>
            <EmptyState v-else description="暂无历史故障" />
          </el-tab-pane>

          <el-tab-pane label="关联部件" name="components">
            <el-table v-if="device.related_components.length" :data="device.related_components" stripe size="small" class="tab-table">
              <el-table-column prop="name" label="部件名称" min-width="180" />
              <el-table-column prop="type" label="类型" min-width="120" />
            </el-table>
            <EmptyState v-else description="暂无关联部件" />
          </el-tab-pane>

          <el-tab-pane label="关联案例" name="cases">
            <el-table v-if="device.related_cases.length" :data="device.related_cases" stripe size="small" class="tab-table">
              <el-table-column prop="title" label="案例标题" min-width="200" />
              <el-table-column prop="symptom" label="相关症状" min-width="150" />
              <el-table-column prop="resolution" label="解决方案" min-width="200" show-overflow-tooltip />
            </el-table>
            <EmptyState v-else description="暂无关联案例" />
          </el-tab-pane>

          <el-tab-pane label="关联草案" name="drafts">
            <el-table v-if="device.related_drafts.length" :data="device.related_drafts" stripe size="small" class="tab-table">
              <el-table-column label="草案编号" min-width="110">
                <template #default="{ row }"><span class="mono id-link" @click="goToDraft(row.id)">{{ row.id }}</span></template>
              </el-table-column>
              <el-table-column prop="fault_diagnosis" label="故障判断" min-width="200" show-overflow-tooltip />
              <el-table-column label="状态" min-width="100">
                <template #default="{ row }"><el-tag v-if="row.status === 'pending_review'" type="warning" size="small">待确认</el-tag><el-tag v-else type="success" size="small">已确认</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" min-width="80">
                <template #default="{ row }"><button class="table-action" @click="goToDraft(row.id)">查看</button></template>
              </el-table-column>
            </el-table>
            <EmptyState v-else description="暂无关联草案" />
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>
  </div>
</template>

<style scoped>
.filter-button { height:32px; padding:0 12px; border:1px solid var(--line-strong); color:var(--muted); background:transparent; font-size:12px; cursor:pointer; }
.filter-button:hover { border-color:var(--muted); color:var(--white); }
.primary-button { height:32px; padding:0 14px; border:1px solid var(--cyan); color:#d9f2ef; background:#21423f; font-size:12px; cursor:pointer; }
.primary-button:hover { background:#295550; }
.id-link { color:var(--cyan-light); font-family:var(--font-mono); cursor:pointer; }
.id-link:hover { color:var(--white); }
.metric-num { color:var(--white); font-family:var(--font-mono); }
.value-red { color:var(--red); }
.value-amber { color:var(--amber); }
.table-action { border:0; padding:0; background:transparent; color:var(--cyan-light); font-size:12px; cursor:pointer; }
.table-action:hover { color:var(--white); }
.detail-tabs { padding:0 18px; }
.tab-table { margin:0; }
</style>
