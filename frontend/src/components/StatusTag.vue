<script setup lang="ts">
/**
 * 设备状态标签 -- 色点 + 中文状态文字
 */
defineProps<{ status: string }>()
</script>

<template>
  <span class="status-tag" :class="{ warning: status === 'warning', fault: status === 'fault' }">
    <i></i>
    <template v-if="status === 'normal'">正常</template>
    <template v-else-if="status === 'warning'">预警</template>
    <template v-else-if="status === 'fault'">故障</template>
    <template v-else>{{ status }}</template>
  </span>
</template>
