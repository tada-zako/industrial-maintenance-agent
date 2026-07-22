<script setup lang="ts">
defineProps<{
  description?: string
}>()
</script>

<template>
  <div class="empty-state">
    <el-empty :description="description || '暂无数据'" />
  </div>
</template>

<style scoped>
.empty-state {
  padding: 32px 0;
  border: 1px solid var(--ui-border);
  background: var(--ui-panel);
}
</style>
