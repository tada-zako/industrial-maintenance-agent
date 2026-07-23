<script setup lang="ts">
defineProps<{ text?: string }>()
</script>

<template>
  <div class="flex items-center gap-3 py-12 justify-center text-[var(--muted)]">
    <span class="inline-block w-5 h-5 border-2 border-[var(--cyan)] border-t-transparent rounded-full animate-spin"></span>
    <span class="text-sm">{{ text || '加载中...' }}</span>
  </div>
</template>
