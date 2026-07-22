<script setup lang="ts">
/**
 * 维修草案详情页 -- 故障判断、检查/维修步骤、安全事项、知识图谱证据、关联工作流
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { MaintenanceDraft } from '../types'
import { fetchDraftDetail, isMockEnabled, updateDraftStatus } from '../api'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'

const route = useRoute()
const router = useRouter()
const draftId = computed(() => route.params.draftId as string)

const draft = ref<MaintenanceDraft | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const workflowId = computed(() => {
  if (!draft.value) return undefined
  if (draft.value.workflow_run_id) return draft.value.workflow_run_id
  // 仅保留旧 Mock 数据的演示映射；真实后端始终使用 workflow_run_id。
  if (!isMockEnabled()) return undefined
  return draft.value.id === 'draft-002' ? 'wf-002' : 'wf-001'
})

async function loadDetail() {
  loading.value = true
  error.value = null
  try {
    draft.value = await fetchDraftDetail(draftId.value)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(status: string) {
  if (!draft.value) return
  try {
    await updateDraftStatus(draft.value.id, status)
    draft.value.status = status as MaintenanceDraft['status']
    ElMessage.success(status === 'confirmed' ? '草案已确认' : '草案已归档')
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

// 从 draft 查找关联工作流
function goToWorkflow() {
  if (workflowId.value) router.push(`/workflows/${workflowId.value}`)
}

onMounted(loadDetail)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-button text @click="router.push('/drafts')">
          <el-icon><svg viewBox="0 0 24 24" width="16" height="16"><path d="M19 12H5M12 19l-7-7 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          返回列表
        </el-button>
        <h2>草案详情</h2>
      </div>
      <div style="display: flex; gap: 8px;">
        <el-button v-if="draft?.status === 'pending_review'" type="success" @click="handleStatusChange('confirmed')">确认草案</el-button>
        <el-button v-if="draft?.status !== 'archived'" @click="handleStatusChange('archived')">归档</el-button>
      </div>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDetail" />

    <template v-else-if="draft">
      <!-- 头部信息 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="草案编号">
            <span class="mono" style="color: var(--color-accent)">{{ draft.id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="关联设备">{{ draft.device_name }}</el-descriptions-item>
          <el-descriptions-item label="风险等级"><SeverityTag :severity="draft.risk_level" /></el-descriptions-item>
          <el-descriptions-item label="草案状态">
            <el-tag v-if="draft.status === 'pending_review'" type="warning" size="small">待确认</el-tag>
            <el-tag v-else-if="draft.status === 'confirmed'" type="success" size="small">已确认</el-tag>
            <el-tag v-else type="info" size="small">已归档</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="需人工确认">
            <el-tag :type="draft.needs_confirmation ? 'warning' : 'success'" size="small">
              {{ draft.needs_confirmation ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            <span class="mono" style="font-size: 12px;">{{ new Date(draft.generated_at).toLocaleString('zh-CN') }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 故障判断 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header><span style="font-weight: 600;">故障判断</span></template>
        <p style="color: var(--color-text-primary); line-height: 1.8; font-size: 14px;">{{ draft.fault_diagnosis }}</p>
      </el-card>

      <el-row :gutter="16">
        <!-- 可能原因 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 16px; height: 100%;">
            <template #header><span style="font-weight: 600;">可能原因</span></template>
            <ol style="padding-left: 20px; color: var(--color-text-secondary); line-height: 2;">
              <li v-for="(cause, idx) in draft.possible_causes" :key="idx">{{ cause }}</li>
            </ol>
          </el-card>
        </el-col>

        <!-- 工具和备件 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 16px; height: 100%;">
            <template #header><span style="font-weight: 600;">所需工具和备件</span></template>
            <ul style="padding-left: 20px; color: var(--color-text-secondary); line-height: 2;">
              <li v-for="(item, idx) in draft.tools_and_parts" :key="idx">{{ item }}</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <!-- 检查步骤 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 16px;">
            <template #header><span style="font-weight: 600;">检查步骤</span></template>
            <el-timeline>
              <el-timeline-item
                v-for="(step, idx) in draft.check_steps" :key="'c'+idx"
                :timestamp="`步骤 ${idx + 1}`" placement="top"
                color="var(--color-info)"
              >
                <p style="color: var(--color-text-secondary); font-size: 13px;">{{ step }}</p>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <!-- 维修步骤 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 16px;">
            <template #header><span style="font-weight: 600;">维修步骤</span></template>
            <el-timeline>
              <el-timeline-item
                v-for="(step, idx) in draft.repair_steps" :key="'r'+idx"
                :timestamp="`步骤 ${idx + 1}`" placement="top"
                color="var(--color-warning)"
              >
                <p style="color: var(--color-text-secondary); font-size: 13px;">{{ step }}</p>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>

      <!-- 安全注意事项 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header><span style="font-weight: 600; color: var(--color-danger);">安全注意事项</span></template>
        <ul style="padding-left: 20px; color: var(--color-text-secondary); line-height: 2.2;">
          <li v-for="(safety, idx) in draft.safety_notices" :key="idx">{{ safety }}</li>
        </ul>
      </el-card>

      <!-- 知识图谱证据 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header><span style="font-weight: 600;">知识图谱证据引用</span></template>
        <el-table v-if="draft.evidence_refs.length" :data="draft.evidence_refs" stripe size="small">
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.type === 'case'" type="success" size="small">案例</el-tag>
              <el-tag v-else-if="row.type === 'sop'" type="warning" size="small">SOP</el-tag>
              <el-tag v-else-if="row.type === 'safety'" type="danger" size="small">安全</el-tag>
              <el-tag v-else type="info" size="small">资料</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="label" label="名称" min-width="200" />
          <el-table-column label="关系" width="150">
            <template #default="{ row }">
              <span class="mono" style="font-size: 12px; color: var(--color-accent)">{{ row.relationship }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="无证据引用" :image-size="60" />
      </el-card>

      <!-- 关联工作流 -->
      <el-card shadow="never">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600;">关联工作流</span>
            <el-button v-if="workflowId" text type="primary" size="small" @click="goToWorkflow">查看工作流详情</el-button>
          </div>
        </template>
        <p style="color: var(--color-text-secondary); font-size: 13px;">
          <template v-if="workflowId">该维修草案由 Agent 工作流自动生成，点击上方按钮可查看完整的多工具调用时间线。</template>
          <template v-else>当前草案没有关联工作流记录，可能来自手工录入或旧版演示数据。</template>
        </p>
      </el-card>
    </template>
  </div>
</template>
