<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

/** 侧边导航菜单项 */
const menuItems = [
  { path: '/overview', label: '运维总览', icon: 'Odometer' },
  { path: '/devices', label: '设备管理', icon: 'Monitor' },
  { path: '/problems', label: '问题中心', icon: 'Warning' },
  { path: '/drafts', label: '维修草案', icon: 'Document' },
  { path: '/materials', label: '运维资料', icon: 'Folder' },
  { path: '/chat', label: 'Hermes 助手', icon: 'ChatDotRound' },
]

function navigate(path: string) {
  router.push(path)
}

function isActive(path: string): boolean {
  if (path === '/overview') return route.path === '/overview'
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" width="28" height="28"><path fill="var(--color-accent)" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <div class="brand-text">
          <h1>工业运维 Agent</h1>
          <span>Maintenance Dashboard</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          @click="navigate(item.path)"
        >
          <el-icon :size="18">
            <svg v-if="item.icon === 'Odometer'" viewBox="0 0 24 24" width="18" height="18"><rect x="2" y="13" width="4" height="9" rx="1" fill="currentColor"/><rect x="10" y="7" width="4" height="15" rx="1" fill="currentColor"/><rect x="18" y="2" width="4" height="20" rx="1" fill="currentColor"/></svg>
            <svg v-else-if="item.icon === 'Monitor'" viewBox="0 0 24 24" width="18" height="18"><rect x="2" y="3" width="20" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" fill="none"/></svg>
            <svg v-else-if="item.icon === 'Warning'" viewBox="0 0 24 24" width="18" height="18"><path d="M12 2L1 21h22L12 2zm0 4.5l7.5 12h-15l7.5-12z" fill="currentColor"/><circle cx="12" cy="16" r="1.5" fill="var(--color-bg-secondary)"/><rect x="11" y="9" width="2" height="5" rx="0.5" fill="var(--color-bg-secondary)"/></svg>
            <svg v-else-if="item.icon === 'Document'" viewBox="0 0 24 24" width="18" height="18"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 2v6h6" fill="none" stroke="currentColor" stroke-width="2"/><line x1="8" y1="13" x2="16" y2="13" stroke="currentColor" stroke-width="2"/><line x1="8" y1="17" x2="16" y2="17" stroke="currentColor" stroke-width="2"/></svg>
            <svg v-else-if="item.icon === 'Folder'" viewBox="0 0 24 24" width="18" height="18"><path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 9h18" stroke="currentColor" stroke-width="2"/></svg>
            <svg v-else-if="item.icon === 'ChatDotRound'" viewBox="0 0 24 24" width="18" height="18"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="10" r="1.5" fill="currentColor"/></svg>
          </el-icon>
          <span>{{ item.label }}</span>
        </div>
      </nav>
      <div class="sidebar-footer">
        <span class="mono">v1.0.0</span>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  user-select: none;
}

.sidebar-brand {
  padding: 20px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--color-border);
}

.brand-icon {
  flex-shrink: 0;
}

.brand-text h1 {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.3;
}

.brand-text span {
  font-size: 11px;
  color: var(--color-text-dim);
  letter-spacing: 0.5px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 14px;
}

.nav-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: rgba(56, 189, 248, 0.1);
  color: var(--color-accent);
  font-weight: 600;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--color-border);
  font-size: 11px;
  color: var(--color-text-dim);
}

/* 主内容区 */
.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
