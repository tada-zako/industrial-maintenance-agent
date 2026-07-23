<script setup lang="ts">
/**
 * 设备列表页 -- 筛选、分页、新增/修改/归档
 * 基于设计稿重构
 */
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Device, DeviceFormData } from '../types'
import { fetchDevices, createDevice, updateDevice, archiveDevice } from '../api'
import StatusTag from '../components/StatusTag.vue'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
const route = useRoute()

const devices = ref<Device[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

const searchKeyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = 10

const dialogVisible = ref(false)
const dialogTitle = ref('新增设备')
const editingId = ref<string | null>(null)
const formData = ref<DeviceFormData>({
  name: '', model: '', area: '', status: 'normal',
  rated_pressure: 0.8, rated_power: 75, commissioned_at: '',
})
const formLoading = ref(false)

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

function onSearch() { currentPage.value = 1; loadDevices() }
function onStatusFilterChange() { currentPage.value = 1; loadDevices() }
function onPageChange(page: number) { currentPage.value = page; loadDevices() }

function openCreateDialog() {
  dialogTitle.value = '新增设备'
  editingId.value = null
  formData.value = { name: '', model: '', area: '', status: 'normal', rated_pressure: 0.8, rated_power: 75, commissioned_at: '' }
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
  } catch { /* 取消 */ }
}

function goToDetail(id: string) { router.push(`/devices/${id}`) }

onMounted(() => {
  if (route.query.status) { statusFilter.value = route.query.status as string }
  loadDevices()
})
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <section class="page-intro">
      <div>
        <span class="page-eyebrow">devices · equipment ledger</span>
        <h1 class="page-heading">设备管理</h1>
      </div>
      <div class="page-updated">{{ new Date().toLocaleDateString('zh-CN') }} · {{ devices.length }} 台设备</div>
    </section>

    <!-- 设备面板（含筛选栏 + 表格） -->
    <section class="app-panel">
      <header class="app-panel__head">
        <span class="app-panel__title">设备台账</span>
        <span class="app-panel__code">{{ total }} RECORDS</span>
      </header>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <input
          v-model="searchKeyword" placeholder="搜索设备名称、编号或型号" class="search-input"
          @keyup.enter="onSearch"
        />
        <button class="filter-button" @click="onStatusFilterChange">全部状态</button>
        <el-select v-model="statusFilter" placeholder="设备状态" clearable
          style="width: 130px;" @change="onStatusFilterChange">
          <el-option label="正常" value="normal" />
          <el-option label="预警" value="warning" />
          <el-option label="故障" value="fault" />
        </el-select>
        <button class="primary-button ml-auto" @click="openCreateDialog">＋ 新增设备</button>
      </div>

      <!-- 数据表格 -->
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" @retry="loadDevices" />
      <template v-else>
        <el-table v-if="devices.length" :data="devices" stripe size="small">
          <el-table-column label="设备编号" min-width="110">
            <template #default="{ row }">
              <span class="mono id-link" @click="goToDetail(row.id)">{{ row.id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="设备名称" min-width="150">
            <template #default="{ row }"><span class="name">{{ row.name }}</span></template>
          </el-table-column>
          <el-table-column prop="model" label="型号" min-width="180" show-overflow-tooltip />
          <el-table-column prop="area" label="所属区域" min-width="140" />
          <el-table-column label="运行状态" min-width="90">
            <template #default="{ row }"><StatusTag :status="row.status" /></template>
          </el-table-column>
          <el-table-column label="排气压力" min-width="130">
            <template #default="{ row }">
              <span class="mono metric-num" :class="{ 'value-red': row.status === 'fault' }">
                {{ row.running_indicators?.exhaust_pressure?.toFixed(2) ?? '-' }} MPa
              </span>
            </template>
          </el-table-column>
          <el-table-column label="温度" min-width="100">
            <template #default="{ row }">
              <span class="mono metric-num" :class="{ 'value-amber': row.status === 'warning', 'value-red': row.status === 'fault' }">
                {{ row.running_indicators?.temperature ?? '-' }} °C
              </span>
            </template>
          </el-table-column>
          <el-table-column label="振动" min-width="100">
            <template #default="{ row }">
              <span class="mono metric-num" :class="{ 'value-amber': row.status === 'warning', 'value-red': row.status === 'fault' }">
                {{ row.running_indicators?.vibration?.toFixed(1) ?? '-' }} mm/s
              </span>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" min-width="170">
            <template #default="{ row }">
              <span class="mono text-xs text-[var(--quiet)]">
                {{ new Date(row.updated_at).toLocaleString('zh-CN') }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="150" fixed="right">
            <template #default="{ row }">
              <button class="table-action" @click="goToDetail(row.id)">详情</button>
              <button class="table-action secondary" @click="openEditDialog(row)">编辑</button>
              <button class="table-action secondary" style="color: var(--red)" @click="handleArchive(row)">停用</button>
            </template>
          </el-table-column>
        </el-table>
        <EmptyState v-else description="暂无设备数据，可点击「新增设备」添加" />

        <!-- 分页 -->
        <div class="flex justify-end p-4 border-t border-[var(--line)]" v-if="total > pageSize">
          <el-pagination
            background layout="total, prev, pager, next"
            :total="total" :page-size="pageSize"
            v-model:current-page="currentPage" @current-change="onPageChange"
          />
        </div>
      </template>
    </section>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form :model="formData" label-width="100px" label-position="left">
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
          <el-select v-model="formData.status" style="width: 100%">
            <el-option label="正常" value="normal" />
            <el-option label="预警" value="warning" />
            <el-option label="故障" value="fault" />
          </el-select>
        </el-form-item>
        <el-form-item label="额定压力(MPa)">
          <el-input-number v-model="formData.rated_pressure" :min="0" :step="0.1" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="额定功率(kW)">
          <el-input-number v-model="formData.rated_power" :min="0" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="投用日期">
          <el-date-picker v-model="formData.commissioned_at" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
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
.search-input {
  height: 32px;
  min-width: 218px;
  padding: 0 10px;
  color: var(--white);
  background: #121212;
  border: 1px solid var(--line);
  outline: none;
  font-size: 13px;
}

.search-input:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 0 2px rgba(79,168,161,.12);
}

.filter-button {
  height: 32px;
  padding: 0 11px;
  border: 1px solid var(--line-strong);
  color: var(--muted);
  background: transparent;
  font-size: 12px;
  cursor: pointer;
}

.filter-button:hover {
  border-color: var(--muted);
  color: var(--white);
}

.primary-button {
  height: 32px;
  padding: 0 14px;
  border: 1px solid var(--cyan);
  color: #d9f2ef;
  background: #21423f;
  font-size: 12px;
  cursor: pointer;
}

.primary-button:hover {
  background: #295550;
}

/* 表格内联样式类 */
.id-link {
  color: var(--cyan-light);
  font-family: var(--font-mono);
  cursor: pointer;
}

.id-link:hover { color: var(--white); }

.name { color: var(--white); font-weight: 500; }

.metric-num { color: var(--white); font-family: var(--font-mono); font-size: 12px; }

.value-red { color: var(--red); }
.value-amber { color: var(--amber); }

.table-action {
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--cyan-light);
  font-size: 12px;
  cursor: pointer;
}

.table-action.secondary {
  color: var(--muted);
  margin-left: 13px;
}

.table-action:hover { color: var(--white); }
</style>
