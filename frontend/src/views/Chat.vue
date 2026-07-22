<script setup lang="ts">
/**
 * Hermes 入口页 -- 跳转 Hermes UI
 */
import { ref, onMounted } from 'vue'
import { checkHealth } from '../api'

const hermesUrl = import.meta.env.VITE_HERMES_WEB_URL || 'http://127.0.0.1:8642'

const agentStatus = ref<'checking' | 'online' | 'offline'>('checking')

const exampleQuestions = [
  '空压机 C-2 排气压力骤降、温度升高，帮我分析原因',
  'A区的空压机有哪些预警信号？',
  '螺杆空压机振动异常通常是什么原因？',
  '请帮我生成空压机 A-2 的检修方案',
  '最近一周有哪些设备出现过故障？',
]

async function checkAgentStatus() {
  agentStatus.value = 'checking'
  const ok = await checkHealth()
  agentStatus.value = ok ? 'online' : 'offline'
}

function openHermes() {
  window.open(hermesUrl, '_blank')
}

function copyQuestion(q: string) {
  navigator.clipboard.writeText(q).catch(() => {})
  openHermes()
}

onMounted(checkAgentStatus)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>Hermes Agent 助手</h2>
    </div>

    <!-- Agent 状态卡片 -->
    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="8">
        <el-card shadow="never" class="agent-card">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div class="agent-icon">
              <svg viewBox="0 0 24 24" width="36" height="36"><path fill="var(--color-accent)" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </div>
            <div>
              <h3 style="font-size: 16px; font-weight: 600;">Hermes Agent</h3>
              <p style="font-size: 13px; color: var(--color-text-secondary);">AI 驱动工业运维智能体</p>
            </div>
          </div>
          <div style="margin-top: 16px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 13px; color: var(--color-text-dim);">服务状态：</span>
            <template v-if="agentStatus === 'checking'">
              <el-icon class="is-loading" style="color: var(--color-warning);"><svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg></el-icon>
              <span style="color: var(--color-warning); font-size: 13px;">检测中...</span>
            </template>
            <template v-else-if="agentStatus === 'online'">
              <span class="status-dot normal" />
              <span style="color: var(--color-success); font-size: 13px;">在线</span>
            </template>
            <template v-else>
              <span class="status-dot fault" />
              <span style="color: var(--color-danger); font-size: 13px;">离线</span>
            </template>
            <el-button text size="small" @click="checkAgentStatus" style="margin-left: auto;">重新检测</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="agent-card">
          <div class="agent-feature">
            <h4>多工具调用</h4>
            <p>Agent 可调用设备查询、故障检索、知识图谱、资料检索、草案生成、校验等多个 MCP 工具</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="agent-card">
          <div class="agent-feature">
            <h4>知识图谱增强</h4>
            <p>基于 Neo4j 知识图谱，关联设备、故障、措施、案例，提供可追溯的推理证据</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 跳转按钮 -->
    <el-card shadow="never" style="margin-bottom: 24px; text-align: center; padding: 32px 0;">
      <h3 style="margin-bottom: 12px; font-size: 18px;">进入 Hermes 对话页面</h3>
      <p style="color: var(--color-text-secondary); margin-bottom: 24px; font-size: 14px;">
        在专用对话界面中与 Agent 交互，获取设备诊断、故障分析和维修建议
      </p>
      <el-button type="primary" size="large" @click="openHermes" :disabled="agentStatus === 'offline'">
        打开 Hermes UI
      </el-button>
      <p v-if="agentStatus === 'offline'" style="color: var(--color-danger); margin-top: 12px; font-size: 13px;">
        Agent 服务离线，请检查 Hermes 是否已启动（端口 {{ hermesUrl.split(':').pop() }}）
      </p>
    </el-card>

    <!-- 示例问题 -->
    <el-card shadow="never">
      <template #header><span style="font-weight: 600;">示例问题</span></template>
      <p style="color: var(--color-text-dim); font-size: 13px; margin-bottom: 12px;">
        点击以下问题可复制到剪贴板并打开 Hermes 对话页面：
      </p>
      <div class="example-questions">
        <div
          v-for="(q, idx) in exampleQuestions" :key="idx"
          class="example-item" @click="copyQuestion(q)"
        >
          <span class="mono" style="font-size: 12px; color: var(--color-text-dim); margin-right: 8px;">#{{ idx + 1 }}</span>
          <span>{{ q }}</span>
          <el-icon style="margin-left: auto; color: var(--color-text-dim);">
            <svg viewBox="0 0 24 24" width="16" height="16"><rect x="9" y="9" width="13" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          </el-icon>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.agent-card {
  height: 100%;
  min-height: 140px;
}

.agent-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(56, 189, 248, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-feature h4 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}

.agent-feature p {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.example-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 14px;
}

.example-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-accent);
}
</style>
