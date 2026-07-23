<script setup lang="ts">
import { computed } from 'vue'
import type { DeviceStatus } from '../types'

const props = defineProps<{
  status: DeviceStatus | string
}>()

const statusMap: Record<string, { text: string; type: '' | 'success' | 'warning' | 'danger' }> = {
  normal: { text: '正常', type: 'success' },
  warning: { text: '预警', type: 'warning' },
  fault: { text: '故障', type: 'danger' },
}

const current = computed(() => statusMap[props.status] || { text: props.status, type: '' as const })
</script>

<template>
  <el-tag :type="current.type" size="small" effect="plain" class="status-tag">
    <span class="status-dot" :class="status" />{{ current.text }}
  </el-tag>
</template>

<style scoped>
.status-tag { border-radius: 2px; font-weight: 500; }
</style>
