<script setup lang="ts">
/**
 * Agent 工作流详情页 -- 多工具调用时间线
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { WorkflowRun } from '../types'
import { fetchWorkflowDetail } from '../api'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'

const route = useRoute()
const router = useRouter()
const runId = computed(() => route.params.runId as string)

const workflow = ref<WorkflowRun | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const stepStatusColor: Record<string, string> = {
  pending: '#5a6d7e',
  in_progress: '#eab308',
  completed: '#22c55e',
  failed: '#ef4444',
  skipped: '#8899aa',
}

const stepStatusLabel: Record<string, string> = {
  pending: '等待中',
  in_progress: '执行中',
  completed: '已完成',
  failed: '失败',
  skipped: '已跳过',
}

async function loadDetail() {
  loading.value = true
  error.value = null
  try {
    workflow.value = await fetchWorkflowDetail(runId.value)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const totalDuration = computed(() => {
  if (!workflow.value?.started_at || !workflow.value?.finished_at) return '-'
  const ms = new Date(workflow.value.finished_at).getTime() - new Date(workflow.value.started_at).getTime()
  const min = Math.floor(ms / 60000)
  const sec = Math.floor((ms % 60000) / 1000)
  return `${min}分${sec}秒`
})

onMounted(loadDetail)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: 12px;">
        <el-button text @click="router.back()">
          <el-icon><svg viewBox="0 0 24 24" width="16" height="16"><path d="M19 12H5M12 19l-7-7 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          返回
        </el-button>
        <h2>Agent 工作流详情</h2>
      </div>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDetail" />

    <template v-else-if="workflow">
      <!-- 工作流概要 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="运行 ID">
            <span class="mono" style="color: var(--color-accent)">{{ workflow.id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="运行状态">
            <el-tag v-if="workflow.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="workflow.status === 'running'" type="warning" size="small">运行中</el-tag>
            <el-tag v-else type="danger" size="small">失败</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标设备">{{ workflow.device_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="总耗时">
            <span class="mono">{{ totalDuration }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            <span class="mono" style="font-size: 12px;">{{ new Date(workflow.started_at).toLocaleString('zh-CN') }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            <span class="mono" style="font-size: 12px;">{{ workflow.finished_at ? new Date(workflow.finished_at).toLocaleString('zh-CN') : '-' }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 用户问题 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <template #header><span style="font-weight: 600;">用户问题</span></template>
        <p style="color: var(--color-text-primary); line-height: 1.8; font-size: 14px;">{{ workflow.user_question }}</p>
      </el-card>

      <!-- 关联草案 -->
      <div v-if="workflow.draft_id" style="margin-bottom: 16px;">
        <el-button type="primary" @click="router.push(`/drafts/${workflow.draft_id}`)">
          查看关联草案 {{ workflow.draft_id }}
        </el-button>
      </div>

      <!-- 多工具调用时间线 -->
      <el-card shadow="never">
        <template #header><span style="font-weight: 600;">多工具调用时间线（{{ workflow.steps.length }} 步）</span></template>
        <el-timeline>
          <el-timeline-item
            v-for="step in workflow.steps" :key="step.id"
            :timestamp="step.step_name"
            placement="top"
            :color="stepStatusColor[step.step_status] || '#5a6d7e'"
            size="large"
          >
            <el-card shadow="never" class="step-card">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-weight: 600;">{{ step.step_name }}</span>
                    <el-tag
                      :type="step.step_status === 'completed' ? 'success' : step.step_status === 'failed' ? 'danger' : 'warning'"
                      size="small"
                    >
                      {{ stepStatusLabel[step.step_status] || step.step_status }}
                    </el-tag>
                  </div>
                  <span class="mono" style="font-size: 11px; color: var(--color-text-dim);">
                    {{ step.started_at ? new Date(step.started_at).toLocaleTimeString('zh-CN') : '-' }}
                    {{ step.finished_at ? ' - ' + new Date(step.finished_at).toLocaleTimeString('zh-CN') : '' }}
                  </span>
                </div>
              </template>

              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item v-if="step.tool_name" label="调用工具">
                  <span class="mono" style="color: var(--color-accent); font-size: 12px;">{{ step.tool_name }}</span>
                </el-descriptions-item>
                <el-descriptions-item v-if="step.tool_input_summary" label="输入">
                  <span style="color: var(--color-text-secondary); font-size: 13px;">{{ step.tool_input_summary }}</span>
                </el-descriptions-item>
                <el-descriptions-item v-if="step.tool_output_summary" label="输出">
                  <span style="color: var(--color-text-secondary); font-size: 13px;">{{ step.tool_output_summary }}</span>
                </el-descriptions-item>
                <el-descriptions-item v-if="step.evidence_used?.length" label="引用证据">
                  <template v-for="(ev, i) in step.evidence_used" :key="i">
                    <el-tag size="small" style="margin-right: 4px; margin-bottom: 4px;">{{ ev }}</el-tag>
                  </template>
                </el-descriptions-item>
                <el-descriptions-item v-if="step.error_info" label="错误信息">
                  <span style="color: var(--color-danger); font-size: 13px;">{{ step.error_info }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.step-card {
  background: var(--color-bg-primary) !important;
  border: 1px solid var(--color-border) !important;
}
</style>
