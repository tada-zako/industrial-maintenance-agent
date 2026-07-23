<script setup lang="ts">
defineProps<{
  message?: string
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="error-state">
    <el-result icon="error" :title="message || '加载失败'" sub-title="请检查网络连接或稍后重试">
      <template #extra>
        <el-button type="primary" @click="emit('retry')">重试</el-button>
      </template>
    </el-result>
  </div>
</template>

<style scoped>
.error-state {
  padding: 32px 0;
  border: 1px solid var(--ui-border);
  background: var(--ui-panel);
}
</style>
