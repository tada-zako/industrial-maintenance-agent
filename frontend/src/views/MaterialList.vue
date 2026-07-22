<script setup lang="ts">
/**
 * 外部运维资料页 -- 展示受控资料元数据，并提供最小化导入和删除能力。
 * 资料正文只作为参考证据展示，不在前端执行或解析上传内容。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile, type UploadUserFile } from 'element-plus'
import { deleteMaterial, fetchDevices, fetchMaterials, importMaterial } from '../api'
import type { Device, ExternalMaterial, MaterialType } from '../types'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const materials = ref<ExternalMaterial[]>([])
const devices = ref<Device[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const searchKeyword = ref('')
const materialTypeFilter = ref('')
const referenceOnly = ref(false)

const dialogVisible = ref(false)
const formLoading = ref(false)
const selectedFile = ref<File | null>(null)
const uploadFileList = ref<UploadUserFile[]>([])
const formData = ref({
  source_description: '',
  device_id: '',
  device_model: '',
  is_reference_allowed: true,
})

const detailVisible = ref(false)
const selectedMaterial = ref<ExternalMaterial | null>(null)

const materialTypeLabel: Record<MaterialType, string> = {
  manual: '设备手册',
  sop: '标准流程',
  case: '维修案例',
  external_reference: '外部参考',
  other: '其他',
}

function getMaterialTypeLabel(type: string): string {
  return materialTypeLabel[type as MaterialType] || type
}

const filteredMaterials = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return materials.value
  return materials.value.filter((material) =>
    [material.filename, material.source_description, material.device_model]
      .filter(Boolean)
      .some((value) => value!.toLowerCase().includes(keyword))
  )
})

const deviceNameMap = computed(() => new Map(devices.value.map((device) => [device.id, device.name])))

function resetForm() {
  formData.value = {
    source_description: '',
    device_id: '',
    device_model: '',
    is_reference_allowed: true,
  }
  selectedFile.value = null
  uploadFileList.value = []
}

async function loadMaterials() {
  loading.value = true
  error.value = null
  try {
    const [materialList, deviceList] = await Promise.all([
      fetchMaterials({
        material_type: materialTypeFilter.value || undefined,
        reference_allowed_only: referenceOnly.value,
      }),
      fetchDevices({ page: 1, page_size: 200 }),
    ])
    materials.value = materialList
    devices.value = deviceList.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载资料失败'
  } finally {
    loading.value = false
  }
}

function openImportDialog() {
  resetForm()
  dialogVisible.value = true
}

function handleFileChange(file: UploadFile) {
  selectedFile.value = file.raw ?? null
  uploadFileList.value = file.raw ? [{ name: file.name, url: '' }] : []
}

function handleFileRemove() {
  selectedFile.value = null
  uploadFileList.value = []
}

function handleDeviceChange(deviceId: string) {
  const device = devices.value.find((item) => item.id === deviceId)
  formData.value.device_model = device?.model ?? ''
}

async function handleImport() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择资料文件')
    return
  }
  if (!formData.value.source_description.trim()) {
    ElMessage.warning('请填写资料来源说明')
    return
  }
  formLoading.value = true
  try {
    await importMaterial({
      file: selectedFile.value,
      source_description: formData.value.source_description.trim(),
      device_id: formData.value.device_id || undefined,
      device_model: formData.value.device_model || undefined,
      is_reference_allowed: formData.value.is_reference_allowed,
    })
    ElMessage.success('资料已导入')
    dialogVisible.value = false
    await loadMaterials()
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '资料导入失败')
  } finally {
    formLoading.value = false
  }
}

function showDetail(material: ExternalMaterial) {
  selectedMaterial.value = material
  detailVisible.value = true
}

async function handleDelete(material: ExternalMaterial) {
  try {
    await ElMessageBox.confirm(`确定删除资料「${material.filename}」吗？`, '确认操作', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMaterial(material.id)
    ElMessage.success('资料已删除')
    if (selectedMaterial.value?.id === material.id) detailVisible.value = false
    await loadMaterials()
  } catch {
    // 用户取消删除时不提示错误。
  }
}

onMounted(loadMaterials)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h2>运维资料</h2>
        <p class="page-description">管理 Agent 可参考的设备手册、维修案例和外部资料。</p>
      </div>
      <el-button type="primary" @click="openImportDialog">导入外部资料</el-button>
    </div>

    <el-card shadow="never" class="filter-card">
      <div class="filter-bar">
        <el-input v-model="searchKeyword" clearable placeholder="搜索文件名、来源或型号" style="width: 260px;" />
        <el-select v-model="materialTypeFilter" clearable placeholder="资料类型" style="width: 150px;" @change="loadMaterials">
          <el-option v-for="(label, value) in materialTypeLabel" :key="value" :label="label" :value="value" />
        </el-select>
        <el-checkbox v-model="referenceOnly" @change="loadMaterials">仅显示允许参考资料</el-checkbox>
        <el-button @click="loadMaterials">刷新</el-button>
      </div>
    </el-card>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadMaterials" />
    <template v-else>
      <el-table v-if="filteredMaterials.length" :data="filteredMaterials" stripe size="small" style="margin-top: 16px;">
        <el-table-column label="资料名称" min-width="220">
          <template #default="{ row }"><span class="mono">{{ row.filename }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }"><el-tag size="small" type="info">{{ getMaterialTypeLabel(row.material_type) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="source_description" label="来源说明" min-width="220" show-overflow-tooltip />
        <el-table-column label="关联设备" min-width="150">
          <template #default="{ row }">{{ row.device_id ? (deviceNameMap.get(row.device_id) || `设备 #${row.device_id}`) : '通用资料' }}</template>
        </el-table-column>
        <el-table-column label="参考状态" width="110">
          <template #default="{ row }"><el-tag :type="row.is_reference_allowed ? 'success' : 'warning'" size="small">{{ row.is_reference_allowed ? '允许参考' : '未授权' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="导入时间" width="170">
          <template #default="{ row }"><span class="mono time-text">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else description="暂无符合条件的运维资料" />
    </template>

    <el-dialog v-model="dialogVisible" title="导入外部资料" width="560px" destroy-on-close>
      <el-alert title="支持 md、txt、json、csv、pdf、docx，单个文件不超过 5 MiB。" type="info" :closable="false" style="margin-bottom: 18px;" />
      <el-form :model="formData" label-width="120px" label-position="left">
        <el-form-item label="资料文件" required>
          <el-upload
            :auto-upload="false"
            :limit="1"
            :file-list="uploadFileList"
            accept=".md,.txt,.json,.csv,.pdf,.docx"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="来源说明" required>
          <el-input v-model="formData.source_description" type="textarea" :rows="3" placeholder="如：供应商提供的 CA-55B 维护手册 V3.2" />
        </el-form-item>
        <el-form-item label="关联设备">
          <el-select v-model="formData.device_id" clearable filterable placeholder="可选，选择后自动关联型号" style="width: 100%;" @change="handleDeviceChange">
            <el-option v-for="device in devices" :key="device.id" :label="`${device.name}（${device.model}）`" :value="device.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备型号">
          <el-input v-model="formData.device_model" placeholder="未关联设备时可直接填写型号" />
        </el-form-item>
        <el-form-item label="允许 Agent 参考">
          <el-switch v-model="formData.is_reference_allowed" />
          <span class="form-tip">关闭后仍保存资料，但不会作为自动生成方案的参考资料。</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="资料详情" size="520px">
      <template v-if="selectedMaterial">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="文件名">{{ selectedMaterial.filename }}</el-descriptions-item>
          <el-descriptions-item label="资料类型">{{ getMaterialTypeLabel(selectedMaterial.material_type) }}</el-descriptions-item>
          <el-descriptions-item label="来源说明">{{ selectedMaterial.source_description }}</el-descriptions-item>
          <el-descriptions-item label="关联设备">{{ selectedMaterial.device_id ? (deviceNameMap.get(selectedMaterial.device_id) || `设备 #${selectedMaterial.device_id}`) : '通用资料' }}</el-descriptions-item>
          <el-descriptions-item label="关联型号">{{ selectedMaterial.device_model || '未指定' }}</el-descriptions-item>
          <el-descriptions-item label="参考状态">{{ selectedMaterial.is_reference_allowed ? '允许 Agent 参考' : '仅保存，不自动参考' }}</el-descriptions-item>
          <el-descriptions-item label="导入时间">{{ new Date(selectedMaterial.created_at).toLocaleString('zh-CN') }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedMaterial.content" class="material-content">
          <div class="content-title">可预览文本</div>
          <pre>{{ selectedMaterial.content }}</pre>
        </div>
        <el-alert v-else title="该文件已保存，但当前 Demo 不解析二进制内容。" type="info" :closable="false" style="margin-top: 18px;" />
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.page-description { color: var(--color-text-secondary); font-size: 13px; margin-top: 4px; }
.filter-card { margin-bottom: 16px; }
.filter-bar { margin-bottom: 0; }
.time-text { color: var(--color-text-dim); font-size: 12px; }
.form-tip { color: var(--color-text-dim); font-size: 12px; margin-left: 10px; }
.material-content { margin-top: 20px; }
.content-title { color: var(--color-text-secondary); font-size: 13px; margin-bottom: 8px; }
.material-content pre {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-primary);
  max-height: 360px;
  overflow: auto;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
