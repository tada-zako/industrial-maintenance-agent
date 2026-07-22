<script setup lang="ts">
/**
 * 设备列表页 -- 筛选、分页、新增/修改/归档
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Device, DeviceFormData, DeviceStatus } from '../types'
import { fetchDevices, createDevice, updateDevice, archiveDevice } from '../api'
import StatusTag from '../components/StatusTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const route = useRoute()

// -- 列表状态 --
const devices = ref<Device[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

// -- 筛选 --
const searchKeyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 10

// -- 新建/编辑弹窗 --
const dialogVisible = ref(false)
const dialogTitle = ref('新增设备')
const editingId = ref<string | null>(null)
const formData = ref<DeviceFormData>({
  name: '', model: '', area: '', status: 'normal',
  rated_pressure: 0.8, rated_power: 75, commissioned_at: '',
})
const formLoading = ref(false)

// -- 加载数据 --
async function loadDevices() {
  loading.value = true
  error.value = null
  try {
    const res = await fetchDevices({
      search: searchKeyword.value || undefined,
      status: statusFilter.value || undefined,
      page: currentPage.value,
      page_size: pageSize,
    })
    devices.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// -- 筛选变更 --
function onSearch() {
  currentPage.value = 1
  loadDevices()
}

function onStatusFilterChange() {
  currentPage.value = 1
  loadDevices()
}

function onPageChange(page: number) {
  currentPage.value = page
  loadDevices()
}

// -- CRUD --
function openCreateDialog() {
  dialogTitle.value = '新增设备'
  editingId.value = null
  formData.value = {
    name: '', model: '', area: '', status: 'normal',
    rated_pressure: 0.8, rated_power: 75, commissioned_at: '',
  }
  dialogVisible.value = true
}

function openEditDialog(device: Device) {
  dialogTitle.value = '编辑设备'
  editingId.value = device.id
  formData.value = {
    name: device.name, model: device.model, area: device.area,
    status: device.status, rated_pressure: device.rated_pressure,
    rated_power: device.rated_power, commissioned_at: device.commissioned_at?.split('T')[0] || '',
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  formLoading.value = true
  try {
    if (editingId.value) {
      await updateDevice(editingId.value, { ...formData.value })
      ElMessage.success('设备信息已更新')
    } else {
      await createDevice({ ...formData.value })
      ElMessage.success('设备已添加')
    }
    dialogVisible.value = false
    loadDevices()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    formLoading.value = false
  }
}

async function handleArchive(device: Device) {
  try {
    await ElMessageBox.confirm(
      `确定要停用设备「${device.name}」吗？停用后设备状态将变为"故障"。`,
      '确认操作',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await archiveDevice(device.id)
    ElMessage.success('设备已停用')
    loadDevices()
  } catch {
    // 取消操作
  }
}

function goToDetail(id: string) {
  router.push(`/devices/${id}`)
}

// -- 初始化 --
onMounted(() => {
  if (route.query.status) {
    statusFilter.value = route.query.status as string
  }
  loadDevices()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>设备管理</h2>
      <el-button type="primary" @click="openCreateDialog">新增设备</el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword" placeholder="搜索名称/编号" clearable
        style="width: 220px;" @keyup.enter="onSearch" @clear="onSearch"
      />
      <el-select v-model="statusFilter" placeholder="设备状态" clearable style="width: 140px;" @change="onStatusFilterChange">
        <el-option label="正常" value="normal" />
        <el-option label="预警" value="warning" />
        <el-option label="故障" value="fault" />
      </el-select>
      <el-button @click="onSearch">查询</el-button>
    </div>

    <!-- 数据表格 -->
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadDevices" />
    <template v-else>
      <el-table v-if="devices.length" :data="devices" stripe size="small" style="width: 100%">
        <el-table-column label="设备编号" min-width="110">
          <template #default="{ row }"><span class="mono" style="color: var(--color-accent); cursor: pointer;" @click="goToDetail(row.id)">{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" min-width="140" />
        <el-table-column prop="model" label="型号" min-width="200" show-overflow-tooltip />
        <el-table-column prop="area" label="所属区域" min-width="140" />
        <el-table-column label="状态" min-width="90">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="排气压力(MPa)" min-width="130">
          <template #default="{ row }">
            <span class="mono" :class="{ 'status-fault': row.status === 'fault' }">
              {{ row.running_indicators?.exhaust_pressure?.toFixed(2) ?? '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="温度(°C)" min-width="100">
          <template #default="{ row }">
            <span class="mono" :class="{ 'status-fault': row.status === 'fault', 'status-warning': row.status === 'warning' }">
              {{ row.running_indicators?.temperature ?? '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="振动(mm/s)" min-width="110">
          <template #default="{ row }">
            <span class="mono" :class="{ 'status-fault': row.status === 'fault', 'status-warning': row.status === 'warning' }">
              {{ row.running_indicators?.vibration?.toFixed(1) ?? '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="170">
          <template #default="{ row }">
            <span class="mono" style="font-size: 12px; color: var(--color-text-dim);">
              {{ new Date(row.updated_at).toLocaleString('zh-CN') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="goToDetail(row.id)">详情</el-button>
            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleArchive(row)">停用</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else description="暂无设备数据" />

      <!-- 分页 -->
      <div style="margin-top: 16px; display: flex; justify-content: flex-end;" v-if="total > pageSize">
        <el-pagination
          background layout="total, prev, pager, next"
          :total="total" :page-size="pageSize"
          v-model:current-page="currentPage" @current-change="onPageChange"
        />
      </div>
    </template>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form :model="formData" label-width="110px" label-position="left">
        <el-form-item label="设备名称" required>
          <el-input v-model="formData.name" placeholder="如：空压机 A-1" />
        </el-form-item>
        <el-form-item label="设备型号" required>
          <el-input v-model="formData.model" placeholder="如：SA-75A 螺杆空压机" />
        </el-form-item>
        <el-form-item label="所属区域" required>
          <el-input v-model="formData.area" placeholder="如：A区-冲压车间" />
        </el-form-item>
        <el-form-item label="设备状态" required>
          <el-select v-model="formData.status" style="width: 100%;">
            <el-option label="正常" value="normal" />
            <el-option label="预警" value="warning" />
            <el-option label="故障" value="fault" />
          </el-select>
        </el-form-item>
        <el-form-item label="额定压力(MPa)">
          <el-input-number v-model="formData.rated_pressure" :min="0" :step="0.1" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="额定功率(kW)">
          <el-input-number v-model="formData.rated_power" :min="0" :step="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="投用日期">
          <el-date-picker v-model="formData.commissioned_at" type="date" placeholder="选择日期" style="width: 100%;" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
:deep(.el-table) { border: 1px solid var(--ui-border); }
:deep(.el-table__header-wrapper) { border-bottom: 1px solid var(--ui-border); }
:deep(.el-table .cell) { line-height: 1.5; }
:deep(.el-dialog__header) { margin-right: 0; padding: 18px 20px; border-bottom: 1px solid var(--ui-border); }
:deep(.el-dialog__body) { padding: 22px 20px 10px; }
:deep(.el-dialog__footer) { padding: 14px 20px 18px; border-top: 1px solid var(--ui-border); }
</style>
