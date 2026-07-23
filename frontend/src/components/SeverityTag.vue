<script setup lang="ts">
/**
 * 严重程度标签 -- 色点 + 等宽大写文字
 */
defineProps<{ severity: string }>()
</script>

<template>
  <span class="severity-tag" :class="severity">
    <template v-if="severity === 'critical'">CRITICAL</template>
    <template v-else-if="severity === 'high'">HIGH</template>
    <template v-else-if="severity === 'medium'">MEDIUM</template>
    <template v-else-if="severity === 'low'">LOW</template>
    <template v-else>{{ severity }}</template>
  </span>
</template>
