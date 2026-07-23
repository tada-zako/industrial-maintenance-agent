<script setup lang="ts">
defineProps<{ description?: string }>()
</script>

<template>
  <div class="py-16 text-center">
    <div class="text-[var(--quiet)] mb-3">
      <svg class="mx-auto w-12 h-12 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <rect x="3" y="3" width="18" height="18" rx="1"/>
        <line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/>
      </svg>
    </div>
    <p class="text-[var(--muted)] text-sm">{{ description || '暂无数据' }}</p>
  </div>
</template>
