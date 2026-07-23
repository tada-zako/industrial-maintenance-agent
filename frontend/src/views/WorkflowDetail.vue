<script setup lang="ts">
/**
 * 工作流详情页 -- 真实步骤顺序、工具调用、证据、耗时、错误
 * 基于设计稿重构
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { WorkflowRun } from '../types'
import { fetchWorkflowDetail } from '../api'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const workflowId = computed(() => route.params.workflowId as string)
const workflow = ref<WorkflowRun | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function loadWorkflow() {
  loading.value = true; error.value = null
  try { workflow.value = await fetchWorkflowDetail(workflowId.value) }
  catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function goToDraft(id: string) { router.push(`/drafts/${id}`) }

onMounted(loadWorkflow)
</script>

<template>
  <div>
    <section class="page-intro">
      <div>
        <span class="page-eyebrow">workflow · agent processing</span>
        <h1 class="page-heading">Agent 工作流详情</h1>
      </div>
      <div class="page-updated mono">{{ workflowId }}</div>
    </section>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadWorkflow" />

    <template v-else-if="workflow">
      <!-- 概要 -->
      <section class="app-panel mb-4">
        <header class="app-panel__head"><span class="app-panel__title">运行概要</span><span class="app-panel__code">STATUS: {{ workflow.status }}</span></header>
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="运行ID"><span class="mono text-[var(--cyan-light)]">{{ workflow.id }}</span></el-descriptions-item>
          <el-descriptions-item label="状态">
            <span class="status-tag" :class="{ warning: workflow.status === 'running', fault: workflow.status === 'failed' }"><i></i>{{ workflow.status === 'completed' ? '已完成' : workflow.status === 'running' ? '运行中' : workflow.status === 'failed' ? '失败' : workflow.status }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="关联设备"><span class="text-[var(--white)]">{{ workflow.device_name || workflow.device_id || '-' }}</span></el-descriptions-item>
          <el-descriptions-item label="总耗时"><span class="mono">{{ workflow.total_duration?.toFixed(1) ?? '—' }} 秒</span></el-descriptions-item>
          <el-descriptions-item label="工具调用次数"><span class="mono">{{ workflow.steps?.length ?? 0 }} 次</span></el-descriptions-item>
          <el-descriptions-item label="开始时间" :span="3">
            <span class="mono text-xs">{{ workflow.started_at ? new Date(workflow.started_at).toLocaleString('zh-CN') : '-' }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </section>

      <!-- 用户问题 -->
      <section class="app-panel mb-4" v-if="workflow.user_query">
        <header class="app-panel__head"><span class="app-panel__title">用户问题</span></header>
        <div class="p-4 text-sm text-[var(--muted)] bg-[#181818]">「 {{ workflow.user_query }} 」</div>
      </section>

      <!-- 关联草案 -->
      <section class="app-panel mb-4" v-if="workflow.draft_id">
        <header class="app-panel__head">
          <span class="app-panel__title">关联草案</span>
          <button class="app-link" @click="goToDraft(workflow.draft_id)">查看草案 →</button>
        </header>
        <div class="p-4"><span class="mono text-sm text-[var(--cyan-light)]">{{ workflow.draft_id }}</span></div>
      </section>

      <!-- 工具调用时间线 -->
      <section class="app-panel">
        <header class="app-panel__head"><span class="app-panel__title">工具调用时间线</span><span class="app-panel__code">{{ workflow.steps?.length || 0 }} STEPS</span></header>
        <div class="p-4" v-if="workflow.steps?.length">
          <el-timeline>
            <el-timeline-item
              v-for="(step, index) in workflow.steps"
              :key="index"
              :timestamp="`步骤 ${index + 1}`"
              placement="top"
              :color="step.status === 'completed' ? 'var(--cyan)' : step.status === 'failed' ? 'var(--red)' : 'var(--line-strong)'"
            >
              <div class="text-sm text-[var(--white)] font-medium">{{ step.action || step.title }}</div>
              <div v-if="step.input_summary" class="text-xs text-[var(--muted)] mt-1 mono">输入: {{ step.input_summary }}</div>
              <div v-if="step.output_summary" class="text-xs text-[var(--muted)] mt-1 mono">输出: {{ step.output_summary }}</div>
              <div v-if="step.evidence_refs?.length" class="mt-1">
                <span v-for="ref in step.evidence_refs" :key="ref" class="text-xs mono text-[var(--cyan-light)] bg-[#181818] px-1.5 py-0.5 mr-1 border border-[var(--line)]">{{ ref }}</span>
              </div>
              <div v-if="step.duration !== undefined" class="text-[10px] mono text-[var(--quiet)] mt-1">耗时 {{ step.duration?.toFixed(0) ?? step.duration }} ms</div>
              <div v-if="step.error" class="text-xs text-[var(--red)] mt-1 mono bg-[#1a1515] px-2 py-1 border border-[var(--line)]">ERROR: {{ step.error }}</div>
            </el-timeline-item>
          </el-timeline>
        </div>
        <EmptyState v-else description="暂无步骤记录" />
      </section>
    </template>
  </div>
</template>
