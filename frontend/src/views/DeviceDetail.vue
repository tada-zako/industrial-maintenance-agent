<script setup lang="ts">
/**
 * 设备详情页 -- 基本信息、运行指标、历史状态、故障记录、关联信息
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { DeviceDetail } from '../types'
import { fetchDeviceDetail } from '../api'
import StatusTag from '../components/StatusTag.vue'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'

const route = useRoute()
const router = useRouter()
const deviceId = computed(() => route.params.deviceId as string)

const device = ref<DeviceDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref('indicators')

const hermesUrl = import.meta.env.VITE_HERMES_WEB_URL || 'http://127.0.0.1:9119'

async function loadDetail() {
  loading.value = true
  error.value = null
  try {
    device.value = await fetchDeviceDetail(deviceId.value)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function openHermes() {
  window.open(hermesUrl, '_blank')
}

function goToDraft(draftId: string) {
  router.push(`/drafts/${draftId}`)
}

function goToKnowledge() {
  if (device.value) {
    // 设备名称不是 FaultSymptom 关键词；使用型号可同时加载该型号的案例和完整故障证据。
    router.push({ path: '/knowledge', query: { model: device.value.model } })
  }
}

onMounted(loadDetail)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-button text @click="router.push('/devices')">
          <el-icon><svg viewBox="0 0 24 24" width="16" height="16"><path d="M19 12H5M12 19l-7-7 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          返回列表
        </el-button>
        <h2>{{ device?.name || '设备详情' }}</h2>
      </div>
      <div style="display: flex; gap: 8px;">
        <el-button @click="goToKnowledge">查看关联知识图谱</el-button>
        <el-button type="primary" @click="openHermes">在 Hermes 中询问</el-button>
      </div>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDetail" />

    <template v-else-if="device">
      <!-- 基本信息 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header><span>基本信息</span></template>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="设备编号">
            <span class="mono" style="color: var(--color-accent)">{{ device.id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="设备名称">{{ device.name }}</el-descriptions-item>
          <el-descriptions-item label="当前状态"><StatusTag :status="device.status" /></el-descriptions-item>
          <el-descriptions-item label="设备型号">{{ device.model }}</el-descriptions-item>
          <el-descriptions-item label="所属区域">{{ device.area }}</el-descriptions-item>
          <el-descriptions-item label="额定压力">{{ device.rated_pressure }} MPa</el-descriptions-item>
          <el-descriptions-item label="额定功率">{{ device.rated_power }} kW</el-descriptions-item>
          <el-descriptions-item label="投用日期">{{ device.commissioned_at }}</el-descriptions-item>
          <el-descriptions-item label="最近更新">
            <span class="mono" style="font-size: 12px;">{{ new Date(device.updated_at).toLocaleString('zh-CN') }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-tabs v-model="activeTab">
        <!-- 运行指标 -->
        <el-tab-pane label="当前运行指标" name="indicators">
          <el-card v-if="device.running_indicators" shadow="never">
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="运行状态">{{ device.running_indicators.running_status }}</el-descriptions-item>
              <el-descriptions-item label="排气压力">
                <span class="mono" :class="{ 'status-fault': device.status === 'fault' }">
                  {{ device.running_indicators.exhaust_pressure }} MPa
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="温度">
                <span class="mono" :class="{ 'status-fault': device.status === 'fault', 'status-warning': device.status === 'warning' }">
                  {{ device.running_indicators.temperature }} °C
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="振动">
                <span class="mono" :class="{ 'status-fault': device.status === 'fault', 'status-warning': device.status === 'warning' }">
                  {{ device.running_indicators.vibration }} mm/s
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="油位">{{ device.running_indicators.oil_level }}</el-descriptions-item>
              <el-descriptions-item label="数据来源">{{ device.running_indicators.source }}</el-descriptions-item>
              <el-descriptions-item label="采集时间" :span="2">
                <span class="mono" style="font-size: 12px;">{{ new Date(device.running_indicators.collected_at).toLocaleString('zh-CN') }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
          <el-empty v-else description="暂无运行指标数据" />
        </el-tab-pane>

        <!-- 历史状态 -->
        <el-tab-pane label="历史状态记录" name="history">
          <el-table v-if="device.status_history.length" :data="device.status_history" stripe size="small">
            <el-table-column label="采集时间" width="170">
              <template #default="{ row }">
                <span class="mono" style="font-size: 12px;">{{ new Date(row.collected_at).toLocaleString('zh-CN') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="running_status" label="运行状态" width="100" />
            <el-table-column label="排气压力" width="100">
              <template #default="{ row }"><span class="mono">{{ row.exhaust_pressure }} MPa</span></template>
            </el-table-column>
            <el-table-column label="温度" width="80">
              <template #default="{ row }"><span class="mono">{{ row.temperature }}°C</span></template>
            </el-table-column>
            <el-table-column label="振动" width="80">
              <template #default="{ row }"><span class="mono">{{ row.vibration }}mm/s</span></template>
            </el-table-column>
            <el-table-column prop="oil_level" label="油位" width="80" />
            <el-table-column prop="source" label="来源" width="100" />
          </el-table>
          <el-empty v-else description="暂无历史状态记录" />
        </el-tab-pane>

        <!-- 历史故障 -->
        <el-tab-pane label="历史故障" name="faults">
          <el-table v-if="device.historical_faults.length" :data="device.historical_faults" stripe size="small">
            <el-table-column prop="symptom" label="故障现象" min-width="160" />
            <el-table-column label="严重程度" width="90">
              <template #default="{ row }"><SeverityTag :severity="row.severity" /></template>
            </el-table-column>
            <el-table-column label="发现时间" width="120">
              <template #default="{ row }">
                <span class="mono" style="font-size: 12px;">{{ row.discovered_at?.split('T')[0] ?? row.discovered_at }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'resolved'" type="success" size="small">已解决</el-tag>
                <el-tag v-else-if="row.status === 'repairing'" type="warning" size="small">维修中</el-tag>
                <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          </el-table>
          <el-empty v-else description="暂无历史故障" />
        </el-tab-pane>

        <!-- 关联部件 -->
        <el-tab-pane label="关联部件" name="components">
          <el-table v-if="device.related_components.length" :data="device.related_components" stripe size="small">
            <el-table-column prop="name" label="部件名称" />
            <el-table-column prop="type" label="类型" />
          </el-table>
          <el-empty v-else description="暂无关联部件" />
        </el-tab-pane>

        <!-- 关联案例 -->
        <el-tab-pane label="关联案例" name="cases">
          <el-table v-if="device.related_cases.length" :data="device.related_cases" stripe size="small">
            <el-table-column prop="title" label="案例标题" min-width="200" />
            <el-table-column prop="symptom" label="相关症状" min-width="150" />
            <el-table-column prop="resolution" label="解决方案" min-width="200" show-overflow-tooltip />
          </el-table>
          <el-empty v-else description="暂无关联案例" />
        </el-tab-pane>

        <!-- 关联草案 -->
        <el-tab-pane label="关联草案" name="drafts">
          <el-table v-if="device.related_drafts.length" :data="device.related_drafts" stripe size="small">
            <el-table-column label="草案编号" width="110">
              <template #default="{ row }">
                <span class="mono" style="color: var(--color-accent); cursor: pointer;" @click="goToDraft(row.id)">{{ row.id }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="fault_diagnosis" label="故障判断" min-width="200" show-overflow-tooltip />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'pending_review'" type="warning" size="small">待确认</el-tag>
                <el-tag v-else type="success" size="small">已确认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button text type="primary" size="small" @click="goToDraft(row.id)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无关联草案" />
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>
