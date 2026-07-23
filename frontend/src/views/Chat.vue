<script setup lang="ts">
/**
 * Hermes 入口页 -- 服务状态、跳转入口、示例问题
 * 基于设计稿重构
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { checkHealth } from '../api'

const hermesUrl = import.meta.env.VITE_HERMES_WEB_URL || 'http://127.0.0.1:9119'

const agentOnline = ref<boolean | null>(null)
const checking = ref(true)

async function checkAgentStatus() {
  checking.value = true
  try {
    const health = await checkHealth()
    agentOnline.value = health?.status === 'ok' || health?.hermes === 'running'
  } catch {
    agentOnline.value = false
  } finally {
    checking.value = false
  }
}

function openHermes() {
  window.open(hermesUrl, '_blank')
}

const sampleQuestions = [
  '空压机 C-2 温度偏高，什么原因？',
  '如何制定空压机 A-1 的月保养计划？',
  '显示所有预警设备',
  '查看最近的维修草案',
]

function copyAndOpen(question: string) {
  navigator.clipboard?.writeText(question).catch(() => {})
  const url = new URL(hermesUrl)
  url.searchParams.set('q', question)
  window.open(url.toString(), '_blank')
}

onMounted(checkAgentStatus)
</script>

<template>
  <div>
    <section class="page-intro">
      <div>
        <span class="page-eyebrow">hermes · ai assistant</span>
        <h1 class="page-heading">Hermes 助手</h1>
      </div>
      <div class="page-updated mono">BUILD 1.0.0</div>
    </section>

    <!-- 服务状态 -->
    <section class="app-panel mb-4">
      <header class="app-panel__head"><span class="app-panel__title">Agent 服务状态</span></header>
      <div class="p-4">
        <div class="flex items-center gap-3">
          <span v-if="checking" class="inline-block w-4 h-4 border-2 border-[var(--cyan)] border-t-transparent rounded-full animate-spin"></span>
          <span v-else>
            <span class="status-tag" :class="{ fault: !agentOnline }"><i></i></span>
          </span>
          <span class="text-sm" :class="checking ? 'text-[var(--muted)]' : agentOnline ? 'text-[var(--white)]' : 'text-[var(--red)]'">
            {{ checking ? '检测中...' : agentOnline ? '服务状态正常' : '服务不可用' }}
          </span>
          <button v-if="!checking && !agentOnline" class="app-link text-xs" @click="checkAgentStatus">重新检测</button>
        </div>
        <div v-if="!checking && agentOnline" class="mt-4">
          <button class="primary-button" @click="openHermes">打开 Hermes UI</button>
        </div>
      </div>
    </section>

    <!-- 功能介绍 -->
    <section class="app-panel mb-4">
      <header class="app-panel__head"><span class="app-panel__title">功能介绍</span></header>
      <div class="p-4 grid grid-cols-2 gap-4">
        <div class="p-3 border border-[var(--line)] bg-[#181818]">
          <h3 class="text-sm text-[var(--white)] font-medium mb-1">多工具调用</h3>
          <p class="text-xs text-[var(--muted)]">Agent 可自动选择并调用设备检测、问题搜索、知识图谱查询等工具。</p>
        </div>
        <div class="p-3 border border-[var(--line)] bg-[#181818]">
          <h3 class="text-sm text-[var(--white)] font-medium mb-1">知识图谱增强</h3>
          <p class="text-xs text-[var(--muted)]">基于历史维修案例和设备关系，提供精准的故障判断和维修建议。</p>
        </div>
      </div>
    </section>

    <!-- 示例问题 -->
    <section class="app-panel">
      <header class="app-panel__head"><span class="app-panel__title">示例问题</span><span class="app-panel__code">可直接跳转 Hermes 提问</span></header>
      <div class="p-4 space-y-2">
        <div
          v-for="(q, i) in sampleQuestions" :key="i"
          class="flex items-center justify-between p-3 border border-[var(--line)] bg-[#181818] cursor-pointer hover:bg-[var(--panel-raised)] transition-colors group"
          @click="copyAndOpen(q)"
        >
          <span class="text-sm text-[var(--muted)] group-hover:text-[var(--white)]">{{ q }}</span>
          <span class="text-xs mono text-[var(--quiet)] group-hover:text-[var(--cyan-light)]">跳转 →</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.primary-button { height:32px; padding:0 14px; border:1px solid var(--cyan); color:#d9f2ef; background:#21423f; font-size:12px; cursor:pointer; }
.primary-button:hover { background:#295550; }
</style>
