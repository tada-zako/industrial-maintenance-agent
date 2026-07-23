<script setup lang="ts">
defineProps<{ message?: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="py-16 text-center">
    <div class="text-[var(--red)] mb-3">
      <svg class="mx-auto w-10 h-10 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    </div>
    <p class="text-[var(--muted)] text-sm mb-4">{{ message || '加载失败' }}</p>
    <button
      class="px-4 py-1.5 border border-[var(--line-strong)] text-[var(--muted)] bg-transparent text-xs cursor-pointer
             hover:border-[var(--muted)] hover:text-[var(--white)] transition-colors"
      @click="emit('retry')"
    >
      重试
    </button>
  </div>
</template>
