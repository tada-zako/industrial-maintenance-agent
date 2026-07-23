<script setup lang="ts">
/**
 * 维修草案详情页 -- 故障判断、时间线、安全注意事项、知识图谱证据
 * 基于设计稿重构
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { MaintenanceDraft } from '../types'
import { fetchDraftDetail } from '../api'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const draftId = computed(() => route.params.draftId as string)
const draft = ref<MaintenanceDraft | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function loadDetail() {
  loading.value = true; error.value = null
  try { draft.value = await fetchDraftDetail(draftId.value) }
  catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function goToWorkflow(id: string) { router.push(`/workflows/${id}`) }
function goToDevice(id: string) { router.push(`/devices/${id}`) }

onMounted(loadDetail)
</script>

<template>
  <div>
    <section class="page-intro">
      <div>
        <span class="page-eyebrow">draft · detail</span>
        <div class="flex items-center gap-3">
          <button class="app-link text-xs" @click="router.push('/drafts')">← 返回列表</button>
          <h1 class="page-heading">{{ draft?.fault_diagnosis || '草案详情' }}</h1>
        </div>
      </div>
      <div class="page-updated mono">{{ draftId }} · {{ draft ? new Date(draft.generated_at).toLocaleString('zh-CN') : '' }}</div>
    </section>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDetail" />

    <template v-else-if="draft">
      <!-- 头部信息 -->
      <section class="app-panel mb-4">
        <header class="app-panel__head">
          <span class="app-panel__title">草案信息</span>
          <span class="app-panel__code">{{ draft.status === 'pending_review' ? 'PENDING_REVIEW' : draft.status === 'confirmed' ? 'CONFIRMED' : 'ARCHIVED' }}</span>
        </header>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="关联设备">
            <span class="text-[var(--white)] cursor-pointer mono" @click="goToDevice(draft.device_id)">{{ draft.device_name || draft.device_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="风险等级"><SeverityTag :severity="draft.risk_level" /></el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="draft.status === 'pending_review'" type="warning" size="small">待确认</el-tag>
            <el-tag v-else-if="draft.status === 'confirmed'" type="success" size="small">已确认</el-tag>
            <el-tag v-else type="info" size="small">已归档</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="故障判断" :span="3">
            <span class="text-[var(--white)]">{{ draft.fault_diagnosis }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </section>

      <!-- 可能原因 -->
      <section class="app-panel mb-4" v-if="draft.possible_causes?.length">
        <header class="app-panel__head"><span class="app-panel__title">可能原因</span></header>
        <div class="p-4">
          <ul class="list-disc list-inside text-sm text-[var(--muted)] space-y-1">
            <li v-for="(cause, i) in draft.possible_causes" :key="i">{{ cause }}</li>
          </ul>
        </div>
      </section>

      <!-- 检查/维修步骤时间线 -->
      <section class="app-panel mb-4" v-if="draft.inspection_steps?.length || draft.repair_steps?.length">
        <header class="app-panel__head"><span class="app-panel__title">检查与维修步骤</span></header>
        <div class="p-4">
          <el-timeline v-if="draft.inspection_steps?.length">
            <el-timeline-item
              v-for="(step, i) in draft.inspection_steps"
              :key="'ins-'+i"
              :timestamp="`检查步骤 ${i + 1}`"
              placement="top"
              :color="'var(--cyan)'"
            >
              <div class="text-sm text-[var(--white)]">{{ step.description }}</div>
              <div v-if="step.expected || step.result" class="text-xs text-[var(--muted)] mt-1">
                <template v-if="step.expected">预期: {{ step.expected }}</template>
                <template v-if="step.result"> / 结果: {{ step.result }}</template>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-timeline v-if="draft.repair_steps?.length" style="margin-top: 8px">
            <el-timeline-item
              v-for="(step, i) in draft.repair_steps"
              :key="'rep-'+i"
              :timestamp="`维修步骤 ${i + 1}`"
              placement="top"
              :color="'var(--amber)'"
            >
              <div class="text-sm text-[var(--white)]">{{ step.description }}</div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </section>

      <!-- 工具备件 -->
      <section class="app-panel mb-4" v-if="draft.tools_parts?.length">
        <header class="app-panel__head"><span class="app-panel__title">工具与备件</span></header>
        <div class="p-4">
          <div class="flex flex-wrap gap-2">
            <span v-for="tp in draft.tools_parts" :key="tp" class="px-2 py-1 text-xs border border-[var(--line)] text-[var(--muted)] bg-[#121212]">{{ tp }}</span>
          </div>
        </div>
      </section>

      <!-- 安全注意事项 -->
      <section class="app-panel mb-4" v-if="draft.safety_notes?.length">
        <header class="app-panel__head"><span class="app-panel__title">安全注意事项</span></header>
        <div class="p-4">
          <div v-for="(note, i) in draft.safety_notes" :key="i" class="flex gap-2 mb-2 last:mb-0">
            <span class="text-[var(--amber)] text-sm font-bold mt-0.5">!</span>
            <span class="text-sm text-[var(--muted)]">{{ note }}</span>
          </div>
        </div>
      </section>

      <!-- 知识图谱证据 -->
      <section class="app-panel mb-4" v-if="draft.evidence_refs?.length">
        <header class="app-panel__head">
          <span class="app-panel__title">知识图谱证据</span>
          <span class="app-panel__code">{{ draft.evidence_refs.length }} EVIDENCES</span>
        </header>
        <el-table :data="draft.evidence_refs" size="small" class="w-full">
          <el-table-column prop="source_node" label="来源节点" min-width="140" />
          <el-table-column prop="target_node" label="目标节点" min-width="140" />
          <el-table-column prop="relationship" label="关系" min-width="160" />
          <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        </el-table>
      </section>

      <!-- 关联工作流 -->
      <section class="app-panel" v-if="draft.workflow_id">
        <header class="app-panel__head">
          <span class="app-panel__title">关联工作流</span>
          <button class="app-link" @click="goToWorkflow(draft.workflow_id)">查看完整流程 →</button>
        </header>
        <div class="p-4">
          <span class="mono text-sm text-[var(--cyan-light)]">{{ draft.workflow_id }}</span>
        </div>
      </section>
    </template>
  </div>
</template>
