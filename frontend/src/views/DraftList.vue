<script setup lang="ts">
/**
 * 维修草案列表页 -- 筛选、查看详情
 * 基于设计稿重构
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
  loading.value = true; error.value = null
  try {
    const res = await fetchDrafts({ search: searchKeyword.value || undefined, status: statusFilter.value || undefined, page: currentPage.value, page_size: pageSize })
    drafts.value = res.items; total.value = res.total
  } catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function onSearch() { currentPage.value = 1; loadDrafts() }
function onPageChange(page: number) { currentPage.value = page; loadDrafts() }
function goToDetail(id: string) { router.push(`/drafts/${id}`) }

async function confirmDraft(draft: MaintenanceDraft) {
  try { await updateDraftStatus(draft.id, 'confirmed'); ElMessage.success('草案已确认'); loadDrafts() }
  catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

onMounted(loadDrafts)
</script>

<template>
  <div>
    <section class="page-intro">
      <div><span class="page-eyebrow">drafts · maintenance plans</span><h1 class="page-heading">维修草案</h1></div>
      <div class="page-updated">{{ new Date().toLocaleDateString('zh-CN') }} · {{ total }} 份草案</div>
    </section>

    <section class="app-panel">
      <header class="app-panel__head">
        <span class="app-panel__title">草案清单</span>
        <span class="app-panel__code">{{ total }} DRAFTS</span>
      </header>

      <div class="filter-bar">
        <input v-model="searchKeyword" placeholder="搜索故障判断" class="search-input" @keyup.enter="onSearch" />
        <el-select v-model="statusFilter" placeholder="草案状态" clearable style="width:140px" @change="onSearch">
          <el-option label="待确认" value="pending_review" /><el-option label="已确认" value="confirmed" /><el-option label="已归档" value="archived" />
        </el-select>
      </div>

      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" @retry="loadDrafts" />
      <template v-else>
        <el-table v-if="drafts.length" :data="drafts" stripe size="small">
          <el-table-column label="编号" min-width="100">
            <template #default="{ row }"><span class="mono text-[var(--cyan-light)] cursor-pointer" @click="goToDetail(row.id)">{{ row.id }}</span></template>
          </el-table-column>
          <el-table-column prop="device_name" label="设备" min-width="130" />
          <el-table-column label="故障判断" min-width="300" show-overflow-tooltip>
            <template #default="{ row }"><span class="text-[var(--white)]">{{ row.fault_diagnosis }}</span></template>
          </el-table-column>
          <el-table-column label="风险等级" min-width="110"><template #default="{ row }"><SeverityTag :severity="row.risk_level" /></template></el-table-column>
          <el-table-column label="状态" min-width="90">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'pending_review'" type="warning" size="small">待确认</el-tag>
              <el-tag v-else-if="row.status === 'confirmed'" type="success" size="small">已确认</el-tag>
              <el-tag v-else type="info" size="small">已归档</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="生成时间" min-width="160">
            <template #default="{ row }"><span class="mono text-xs text-[var(--quiet)]">{{ new Date(row.generated_at).toLocaleString('zh-CN') }}</span></template>
          </el-table-column>
          <el-table-column label="操作" min-width="150" fixed="right">
            <template #default="{ row }">
              <button class="table-action" @click="goToDetail(row.id)">详情</button>
              <button v-if="row.status === 'pending_review'" class="table-action secondary" @click="confirmDraft(row)">确认</button>
            </template>
          </el-table-column>
        </el-table>
        <EmptyState v-else description="暂无维修草案" />
        <div class="flex justify-end p-4 border-t border-[var(--line)]" v-if="total > pageSize">
          <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.search-input { height:32px; min-width:218px; padding:0 10px; color:var(--white); background:#121212; border:1px solid var(--line); outline:none; font-size:13px; }
.search-input:focus { border-color:var(--cyan); box-shadow:0 0 0 2px rgba(79,168,161,.12); }
.table-action { border:0; padding:0; background:transparent; color:var(--cyan-light); font-size:12px; cursor:pointer; }
.table-action.secondary { color:var(--muted); margin-left:13px; }
.table-action:hover { color:var(--white); }
</style>
