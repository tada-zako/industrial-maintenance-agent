<script setup lang="ts">
/**
 * 运维资料页 -- 资料列表、导入、删除
 * 基于设计稿重构
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ExternalMaterial } from '../types'
import { fetchMaterials, deleteMaterial, importMaterial } from '../api'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'

const materials = ref<ExternalMaterial[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = 10

const uploadVisible = ref(false)
const uploadForm = ref({ file: null as File | null, source_description: '', device_id: '' })
const uploadLoading = ref(false)

async function loadMaterials() {
  loading.value = true; error.value = null
  try {
    materials.value = await fetchMaterials({})
  } catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function onSearch() { currentPage.value = 1; loadMaterials() }
function onPageChange(page: number) { currentPage.value = page; loadMaterials() }

function handleFileChange(file: any) {
  uploadForm.value.file = file.raw || file
}

async function handleUpload() {
  if (!uploadForm.value.file) { ElMessage.warning('请选择文件'); return }
  uploadLoading.value = true
  try {
    await importMaterial({
      file: uploadForm.value.file,
      source_description: uploadForm.value.source_description,
      device_id: uploadForm.value.device_id || undefined,
      is_reference_allowed: true,
    })
    ElMessage.success('资料导入成功')
    uploadVisible.value = false
    uploadForm.value = { file: null, source_description: '', device_id: '' }
    loadMaterials()
  } catch (e: any) { ElMessage.error(e.message || '导入失败') }
  finally { uploadLoading.value = false }
}

async function handleDelete(material: ExternalMaterial) {
  try {
    await ElMessageBox.confirm(`确定要删除「${material.title || material.file_name}」吗？`, '确认操作', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    await deleteMaterial(material.id)
    ElMessage.success('已删除')
    loadMaterials()
  } catch { /* cancel */ }
}

onMounted(loadMaterials)
</script>

<template>
  <div>
    <section class="page-intro">
      <div><span class="page-eyebrow">materials · documentation</span><h1 class="page-heading">运维资料</h1></div>
      <div class="page-updated">{{ new Date().toLocaleDateString('zh-CN') }} · {{ materials.length }} 份资料</div>
    </section>

    <section class="app-panel">
      <header class="app-panel__head">
        <span class="app-panel__title">资料清单</span>
        <span class="app-panel__code">{{ materials.length }} FILES</span>
      </header>

      <div class="filter-bar">
        <input v-model="searchKeyword" placeholder="搜索资料名称" class="search-input" @keyup.enter="onSearch" />
        <button class="primary-button ml-auto" @click="uploadVisible = true">＋ 导入资料</button>
      </div>

      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" @retry="loadMaterials" />
      <template v-else>
        <el-table v-if="materials.length" :data="materials" stripe size="small">
          <el-table-column label="文件名" min-width="240">
            <template #default="{ row }"><span class="text-[var(--white)]">{{ row.title || row.file_name }}</span></template>
          </el-table-column>
          <el-table-column label="类型" min-width="100">
            <template #default="{ row }"><span class="text-xs text-[var(--muted)]">{{ row.material_type || '未知' }}</span></template>
          </el-table-column>
          <el-table-column label="来源" min-width="130">
            <template #default="{ row }"><span class="text-xs mono text-[var(--quiet)]">{{ row.source }}</span></template>
          </el-table-column>
          <el-table-column label="关联设备" min-width="130">
            <template #default="{ row }">{{ row.related_device || '-' }}</template>
          </el-table-column>
          <el-table-column label="导入时间" min-width="160">
            <template #default="{ row }"><span class="mono text-xs text-[var(--quiet)]">{{ row.imported_at ? new Date(row.imported_at).toLocaleString('zh-CN') : '-' }}</span></template>
          </el-table-column>
          <el-table-column label="操作" min-width="80" fixed="right">
            <template #default="{ row }"><button class="table-action" style="color:var(--red)" @click="handleDelete(row)">删除</button></template>
          </el-table-column>
        </el-table>
        <EmptyState v-else description="暂无运维资料，可点击「导入资料」添加" />
        <div class="flex justify-end p-4 border-t border-[var(--line)]" v-if="materials.length > pageSize">
          <el-pagination background layout="total, prev, pager, next" :total="materials.length" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
        </div>
      </template>
    </section>

    <!-- 导入弹窗 -->
    <el-dialog v-model="uploadVisible" title="导入资料" width="480px" destroy-on-close>
      <el-form label-width="90px" label-position="left">
        <el-form-item label="选择文件" required>
          <el-upload :auto-upload="false" :limit="1" :on-change="handleFileChange" drag>
            <div class="text-center py-4 text-[var(--muted)] text-xs">点击或拖拽文件到此处</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="来源说明"><el-input v-model="uploadForm.source_description" placeholder="如：设备供应商资料" /></el-form-item>
        <el-form-item label="关联设备"><el-input v-model="uploadForm.device_id" placeholder="如：空压机 A-1" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="uploadVisible = false">取消</el-button><el-button type="primary" :loading="uploadLoading" @click="handleUpload">确认导入</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.search-input { height:32px; min-width:218px; padding:0 10px; color:var(--white); background:#121212; border:1px solid var(--line); outline:none; font-size:13px; }
.search-input:focus { border-color:var(--cyan); box-shadow:0 0 0 2px rgba(79,168,161,.12); }
.primary-button { height:32px; padding:0 14px; border:1px solid var(--cyan); color:#d9f2ef; background:#21423f; font-size:12px; cursor:pointer; }
.primary-button:hover { background:#295550; }
.table-action { border:0; padding:0; background:transparent; color:var(--cyan-light); font-size:12px; cursor:pointer; }
.table-action:hover { color:var(--white); }
</style>
