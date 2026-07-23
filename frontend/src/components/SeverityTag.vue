<script setup lang="ts">
import { computed } from 'vue'
import type { ProblemSeverity } from '../types'

const props = defineProps<{
  severity: ProblemSeverity | string
}>()

const severityMap: Record<string, { text: string; type: '' | 'success' | 'warning' | 'danger' | 'info' }> = {
  low: { text: '低', type: 'info' },
  medium: { text: '中', type: 'warning' },
  high: { text: '高', type: 'danger' },
  critical: { text: '严重', type: 'danger' },
}

const current = computed(
  () => severityMap[props.severity] || { text: props.severity, type: '' as const }
)
</script>

<template>
  <el-tag :type="current.type" size="small" effect="plain" class="severity-tag">{{ current.text }}</el-tag>
</template>

<style scoped>
.severity-tag { min-width: 30px; justify-content: center; border-radius: 2px; font-family: var(--font-mono); font-size: 11px; }
</style>
