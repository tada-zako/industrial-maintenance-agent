<script setup lang="ts">
/**
 * 问题列表页 -- 筛选、分页、新增/修改/归档
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Problem, ProblemFormData, ProblemSeverity, ProblemStatus } from '../types'
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

// 新建/编辑弹窗
const dialogVisible = ref(false)
const dialogTitle = ref('新增问题')
const editingId = ref<string | null>(null)
const formData = ref<ProblemFormData>({
  device_id: '', symptom: '', severity: 'medium', status: 'pending',
  description: '', possible_causes: [], source: '人工录入',
})
const formLoading = ref(false)
const causesInput = ref('')

async function loadProblems() {
  loading.value = true
  error.value = null
  try {
    const res = await fetchProblems({
      search: searchKeyword.value || undefined,
      severity: severityFilter.value || undefined,
      status: statusFilter.value || undefined,
      page: currentPage.value,
      page_size: pageSize,
    })
    problems.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function onSearch() { currentPage.value = 1; loadProblems() }
function onPageChange(page: number) { currentPage.value = page; loadProblems() }

function openCreateDialog() {
  dialogTitle.value = '新增问题'
  editingId.value = null
  formData.value = {
    device_id: '', symptom: '', severity: 'medium', status: 'pending',
    description: '', possible_causes: [], source: '人工录入',
  }
  causesInput.value = ''
  dialogVisible.value = true
}

function openEditDialog(problem: Problem) {
  dialogTitle.value = '编辑问题'
  editingId.value = problem.id
  formData.value = {
    device_id: problem.device_id, symptom: problem.symptom,
    severity: problem.severity, status: problem.status,
    description: problem.description, possible_causes: [...problem.possible_causes],
    source: problem.source,
  }
  causesInput.value = problem.possible_causes.join('\n')
  dialogVisible.value = true
}

async function handleSubmit() {
  formData.value.possible_causes = causesInput.value
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
  formLoading.value = true
  try {
    if (editingId.value) {
      await updateProblem(editingId.value, { ...formData.value })
      ElMessage.success('问题信息已更新')
    } else {
      await createProblem({ ...formData.value })
      ElMessage.success('问题已添加')
    }
    dialogVisible.value = false
    loadProblems()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    formLoading.value = false
  }
}

async function handleArchive(problem: Problem) {
  try {
    await ElMessageBox.confirm(
      `确定要归档问题「${problem.symptom}」吗？`,
      '确认操作',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await archiveProblem(problem.id)
    ElMessage.success('问题已归档')
    loadProblems()
  } catch {
    // 取消
  }
}

const statusLabelMap: Record<string, string> = {
  pending: '待处理', investigating: '调查中', repairing: '维修中',
  resolved: '已解决', archived: '已归档',
}
const statusTagType: Record<string, string> = {
  pending: 'info', investigating: 'warning', repairing: 'danger',
  resolved: 'success', archived: 'info',
}

onMounted(loadProblems)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>问题中心</h2>
      <el-button type="primary" @click="openCreateDialog">新增问题</el-button>
    </div>

    <div class="filter-bar">
      <el-input v-model="searchKeyword" placeholder="搜索故障现象" clearable style="width: 200px;" @keyup.enter="onSearch" @clear="onSearch" />
      <el-select v-model="severityFilter" placeholder="严重程度" clearable style="width: 130px;" @change="onSearch">
        <el-option label="严重" value="critical" />
        <el-option label="高" value="high" />
        <el-option label="中" value="medium" />
        <el-option label="低" value="low" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="处理状态" clearable style="width: 130px;" @change="onSearch">
        <el-option label="待处理" value="pending" />
        <el-option label="调查中" value="investigating" />
        <el-option label="维修中" value="repairing" />
        <el-option label="已解决" value="resolved" />
      </el-select>
      <el-button @click="onSearch">查询</el-button>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadProblems" />
    <template v-else>
      <el-table v-if="problems.length" :data="problems" stripe size="small" style="width: 100%">
        <el-table-column label="编号" min-width="100">
          <template #default="{ row }"><span class="mono" style="color: var(--color-accent)">{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column prop="device_name" label="关联设备" min-width="130" />
        <el-table-column prop="symptom" label="故障现象" min-width="260" show-overflow-tooltip />
        <el-table-column label="严重程度" min-width="95">
          <template #default="{ row }"><SeverityTag :severity="row.severity" /></template>
        </el-table-column>
        <el-table-column label="状态" min-width="95">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status] || 'info'" size="small">
              {{ statusLabelMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发现时间" min-width="170">
          <template #default="{ row }">
            <span class="mono" style="font-size: 12px; color: var(--color-text-dim);">
              {{ new Date(row.discovered_at).toLocaleString('zh-CN') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" min-width="100" />
        <el-table-column label="关联草案" min-width="110">
          <template #default="{ row }">
            <span v-if="row.draft_id" class="mono" style="color: var(--color-accent); cursor: pointer;" @click="router.push(`/drafts/${row.draft_id}`)">
              {{ row.draft_id }}
            </span>
            <span v-else style="color: var(--color-text-dim);">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleArchive(row)" v-if="row.status !== 'archived'">归档</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else />

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;" v-if="total > pageSize">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
      </div>
    </template>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
      <el-form :model="formData" label-width="100px" label-position="left">
        <el-form-item label="关联设备" required>
          <el-input v-model="formData.device_id" placeholder="如：dev-001" />
        </el-form-item>
        <el-form-item label="故障现象" required>
          <el-input v-model="formData.symptom" placeholder="如：排气压力持续下降" />
        </el-form-item>
        <el-form-item label="严重程度" required>
          <el-select v-model="formData.severity" style="width: 100%;">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态" required>
          <el-select v-model="formData.status" style="width: 100%;">
            <el-option label="待处理" value="pending" />
            <el-option label="调查中" value="investigating" />
            <el-option label="维修中" value="repairing" />
            <el-option label="已解决" value="resolved" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="可能原因">
          <el-input v-model="causesInput" type="textarea" :rows="3" placeholder="每行一个可能原因" />
        </el-form-item>
        <el-form-item label="数据来源">
          <el-input v-model="formData.source" placeholder="如：PLC报警 / 巡检发现 / 人工录入" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
