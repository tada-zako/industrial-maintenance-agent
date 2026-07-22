<script setup lang="ts">
defineProps<{
  text?: string
}>()
</script>

<template>
  <div class="loading-state">
    <el-icon class="is-loading" :size="32"><svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M512 64a448 448 0 1 0 448 448A448 448 0 0 0 512 64zm0 832a384 384 0 1 1 384-384 384 384 0 0 1-384 384z" fill="currentColor" opacity=".2"/><path d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32z" fill="currentColor"/></svg></el-icon>
    <p>{{ text || '加载中...' }}</p>
  </div>
</template>

<style scoped>
.loading-state {
  display: flex; align-items: center; justify-content: center; min-height: 180px; gap: 10px;
  color: var(--ui-text-muted); font-size: 13px;
}
.loading-state .el-icon { color: var(--ui-accent); }
.loading-state p { margin: 0; }
</style>
