<script setup lang="ts">
/**
 * 维修草案列表页 -- 筛选、查看详情
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { MaintenanceDraft } from '../types'
import { fetchDrafts, updateDraftStatus } from '../api'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()

const drafts = ref<MaintenanceDraft[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

const searchKeyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 10

async function loadDrafts() {
  loading.value = true
  error.value = null
  try {
    const res = await fetchDrafts({
      search: searchKeyword.value || undefined,
      status: statusFilter.value || undefined,
      page: currentPage.value,
      page_size: pageSize,
    })
    drafts.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function onSearch() { currentPage.value = 1; loadDrafts() }
function onPageChange(page: number) { currentPage.value = page; loadDrafts() }

function goToDetail(id: string) {
  router.push(`/drafts/${id}`)
}

async function confirmDraft(draft: MaintenanceDraft) {
  try {
    await updateDraftStatus(draft.id, 'confirmed')
    ElMessage.success('草案已确认')
    loadDrafts()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

const statusLabelMap: Record<string, string> = {
  pending_review: '待确认', confirmed: '已确认', archived: '已归档',
}

onMounted(loadDrafts)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>维修草案</h2>
    </div>

    <div class="filter-bar">
      <el-input v-model="searchKeyword" placeholder="搜索故障判断" clearable style="width: 240px;" @keyup.enter="onSearch" @clear="onSearch" />
      <el-select v-model="statusFilter" placeholder="草案状态" clearable style="width: 140px;" @change="onSearch">
        <el-option label="待确认" value="pending_review" />
        <el-option label="已确认" value="confirmed" />
        <el-option label="已归档" value="archived" />
      </el-select>
      <el-button @click="onSearch">查询</el-button>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDrafts" />
    <template v-else>
      <el-table v-if="drafts.length" :data="drafts" stripe size="small" style="width: 100%">
        <el-table-column label="编号" min-width="100">
          <template #default="{ row }">
            <span class="mono" style="color: var(--color-accent); cursor: pointer;" @click="goToDetail(row.id)">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="device_name" label="设备" min-width="130" />
        <el-table-column prop="fault_diagnosis" label="故障判断" min-width="320" show-overflow-tooltip />
        <el-table-column label="风险等级" min-width="95">
          <template #default="{ row }"><SeverityTag :severity="row.risk_level" /></template>
        </el-table-column>
        <el-table-column label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending_review'" type="warning" size="small">待确认</el-tag>
            <el-tag v-else-if="row.status === 'confirmed'" type="success" size="small">已确认</el-tag>
            <el-tag v-else type="info" size="small">已归档</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="生成时间" min-width="170">
          <template #default="{ row }">
            <span class="mono" style="font-size: 12px; color: var(--color-text-dim);">
              {{ new Date(row.generated_at).toLocaleString('zh-CN') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="goToDetail(row.id)">详情</el-button>
            <el-button v-if="row.status === 'pending_review'" text type="success" size="small" @click="confirmDraft(row)">确认</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else />

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;" v-if="total > pageSize">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
      </div>
    </template>
  </div>
</template>

<style scoped>
:deep(.el-table) { border: 1px solid var(--ui-border); }
:deep(.el-card__header) { border-bottom-color: var(--ui-border); font: 12px var(--font-mono); }
</style>
