<script setup lang="ts">
/**
 * 问题列表页 -- 筛选、分页、新增/修改/归档
 * 基于设计稿重构
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Problem, ProblemFormData } from '../types'
import { fetchProblems, createProblem, updateProblem, archiveProblem } from '../api'
import SeverityTag from '../components/SeverityTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const problems = ref<Problem[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)
const searchKeyword = ref('')
const severityFilter = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 10

const dialogVisible = ref(false)
const dialogTitle = ref('新增问题')
const editingId = ref<string | null>(null)
const formData = ref<ProblemFormData>({ device_id: '', symptom: '', severity: 'medium', status: 'pending', description: '', possible_causes: [], source: '人工录入' })
const formLoading = ref(false)
const causesInput = ref('')

async function loadProblems() {
  loading.value = true; error.value = null
  try {
    const res = await fetchProblems({ search: searchKeyword.value || undefined, severity: severityFilter.value || undefined, status: statusFilter.value || undefined, page: currentPage.value, page_size: pageSize })
    problems.value = res.items; total.value = res.total
  } catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function onSearch() { currentPage.value = 1; loadProblems() }
function onPageChange(page: number) { currentPage.value = page; loadProblems() }

function openCreateDialog() {
  dialogTitle.value = '新增问题'; editingId.value = null
  formData.value = { device_id: '', symptom: '', severity: 'medium', status: 'pending', description: '', possible_causes: [], source: '人工录入' }
  causesInput.value = ''; dialogVisible.value = true
}

function openEditDialog(problem: Problem) {
  dialogTitle.value = '编辑问题'; editingId.value = problem.id
  formData.value = { device_id: problem.device_id, symptom: problem.symptom, severity: problem.severity, status: problem.status, description: problem.description, possible_causes: [...problem.possible_causes], source: problem.source }
  causesInput.value = problem.possible_causes.join('\n'); dialogVisible.value = true
}

async function handleSubmit() {
  formData.value.possible_causes = causesInput.value.split('\n').map(s => s.trim()).filter(Boolean)
  formLoading.value = true
  try {
    if (editingId.value) { await updateProblem(editingId.value, { ...formData.value }); ElMessage.success('问题信息已更新') }
    else { await createProblem({ ...formData.value }); ElMessage.success('问题已添加') }
    dialogVisible.value = false; loadProblems()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
  finally { formLoading.value = false }
}

async function handleArchive(problem: Problem) {
  try {
    await ElMessageBox.confirm(`确定要归档问题「${problem.symptom}」吗？`, '确认操作', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await archiveProblem(problem.id); ElMessage.success('问题已归档'); loadProblems()
  } catch { /* cancel */ }
}

const statusLabelMap: Record<string, string> = { pending: '待处理', investigating: '调查中', repairing: '维修中', resolved: '已解决', archived: '已归档' }
const statusTagType: Record<string, string> = { pending: 'info', investigating: 'warning', repairing: 'danger', resolved: 'success', archived: 'info' }

onMounted(loadProblems)
</script>

<template>
  <div>
    <section class="page-intro">
      <div><span class="page-eyebrow">problems · issue center</span><h1 class="page-heading">问题中心</h1></div>
      <div class="page-updated">{{ new Date().toLocaleDateString('zh-CN') }} · {{ total }} 个问题</div>
    </section>

    <section class="app-panel">
      <header class="app-panel__head">
        <span class="app-panel__title">问题清单</span>
        <span class="app-panel__code">{{ total }} ISSUES</span>
      </header>

      <div class="filter-bar">
        <input v-model="searchKeyword" placeholder="搜索故障现象" class="search-input" @keyup.enter="onSearch" />
        <el-select v-model="severityFilter" placeholder="严重程度" clearable style="width:120px" @change="onSearch">
          <el-option label="严重" value="critical" /><el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="处理状态" clearable style="width:120px" @change="onSearch">
          <el-option label="待处理" value="pending" /><el-option label="调查中" value="investigating" /><el-option label="维修中" value="repairing" /><el-option label="已解决" value="resolved" />
        </el-select>
        <button class="primary-button ml-auto" @click="openCreateDialog">＋ 新增问题</button>
      </div>

      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" @retry="loadProblems" />
      <template v-else>
        <el-table v-if="problems.length" :data="problems" stripe size="small">
          <el-table-column label="编号" min-width="100"><template #default="{ row }"><span class="mono text-[var(--cyan-light)]">{{ row.id }}</span></template></el-table-column>
          <el-table-column prop="device_name" label="关联设备" min-width="130" />
          <el-table-column prop="symptom" label="故障现象" min-width="240" show-overflow-tooltip>
            <template #default="{ row }"><span class="text-[var(--white)]">{{ row.symptom }}</span></template>
          </el-table-column>
          <el-table-column label="严重程度" min-width="110"><template #default="{ row }"><SeverityTag :severity="row.severity" /></template></el-table-column>
          <el-table-column label="状态" min-width="100">
            <template #default="{ row }"><el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ statusLabelMap[row.status] || row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="发现时间" min-width="160">
            <template #default="{ row }"><span class="mono text-xs text-[var(--quiet)]">{{ new Date(row.discovered_at).toLocaleString('zh-CN') }}</span></template>
          </el-table-column>
          <el-table-column label="来源" min-width="90"><template #default="{ row }"><span class="text-[var(--muted)] text-xs">{{ row.source }}</span></template></el-table-column>
          <el-table-column label="关联草案" min-width="110">
            <template #default="{ row }">
              <span v-if="row.draft_id" class="mono text-[var(--cyan-light)] cursor-pointer" @click="router.push(`/drafts/${row.draft_id}`)">{{ row.draft_id }}</span>
              <span v-else class="text-[var(--quiet)]">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="150" fixed="right">
            <template #default="{ row }">
              <button class="table-action" @click="openEditDialog(row)">编辑</button>
              <button class="table-action secondary" style="color:var(--red)" @click="handleArchive(row)" v-if="row.status !== 'archived'">归档</button>
            </template>
          </el-table-column>
        </el-table>
        <EmptyState v-else description="暂无问题记录" />
        <div class="flex justify-end p-4 border-t border-[var(--line)]" v-if="total > pageSize">
          <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
        </div>
      </template>
    </section>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
      <el-form :model="formData" label-width="100px" label-position="left">
        <el-form-item label="关联设备" required><el-input v-model="formData.device_id" placeholder="如：dev-001" /></el-form-item>
        <el-form-item label="故障现象" required><el-input v-model="formData.symptom" placeholder="如：排气压力持续下降" /></el-form-item>
        <el-form-item label="严重程度" required><el-select v-model="formData.severity" style="width:100%"><el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" /></el-select></el-form-item>
        <el-form-item label="处理状态" required><el-select v-model="formData.status" style="width:100%"><el-option label="待处理" value="pending" /><el-option label="调查中" value="investigating" /><el-option label="维修中" value="repairing" /><el-option label="已解决" value="resolved" /></el-select></el-form-item>
        <el-form-item label="问题描述"><el-input v-model="formData.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="可能原因"><el-input v-model="causesInput" type="textarea" :rows="3" placeholder="每行一个可能原因" /></el-form-item>
        <el-form-item label="数据来源"><el-input v-model="formData.source" placeholder="如：PLC报警 / 巡检发现 / 人工录入" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="formLoading" @click="handleSubmit">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.search-input { height:32px; min-width:218px; padding:0 10px; color:var(--white); background:#121212; border:1px solid var(--line); outline:none; font-size:13px; }
.search-input:focus { border-color:var(--cyan); box-shadow:0 0 0 2px rgba(79,168,161,.12); }
.primary-button { height:32px; padding:0 14px; border:1px solid var(--cyan); color:#d9f2ef; background:#21423f; font-size:12px; cursor:pointer; }
.primary-button:hover { background:#295550; }
.table-action { border:0; padding:0; background:transparent; color:var(--cyan-light); font-size:12px; cursor:pointer; }
.table-action.secondary { color:var(--muted); margin-left:13px; }
.table-action:hover { color:var(--white); }
</style>
