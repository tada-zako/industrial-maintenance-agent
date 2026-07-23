<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const pageTitle = computed(() => String(route.meta.title || '工业运维 Agent'))

/** 侧边导航菜单项 */
const menuItems = [
  { path: '/overview', label: '运维总览', icon: 'Odometer', code: '01', group: '工作台' },
  { path: '/devices', label: '设备管理', icon: 'Monitor', code: '02', group: '工作台' },
  { path: '/problems', label: '问题中心', icon: 'Warning', code: '03', group: '工作台' },
  { path: '/drafts', label: '维修草案', icon: 'Document', code: '04', group: '工作台' },
  { path: '/materials', label: '运维资料', icon: 'Folder', code: '05', group: '资料与协作' },
  { path: '/knowledge', label: '知识图谱', icon: 'Share', code: '06', group: '资料与协作' },
  { path: '/chat', label: 'Hermes 助手', icon: 'ChatDotRound', code: '07', group: '资料与协作' },
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
          <span>maintenance console</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <template v-for="(item, index) in menuItems" :key="item.path">
          <span v-if="index === 0 || item.group !== menuItems[index - 1].group" class="nav-caption">{{ item.group }}</span>
          <button class="nav-item" :class="{ active: isActive(item.path) }" @click="navigate(item.path)">
          <el-icon :size="18">
            <svg v-if="item.icon === 'Odometer'" viewBox="0 0 24 24" width="18" height="18"><rect x="2" y="13" width="4" height="9" rx="1" fill="currentColor"/><rect x="10" y="7" width="4" height="15" rx="1" fill="currentColor"/><rect x="18" y="2" width="4" height="20" rx="1" fill="currentColor"/></svg>
            <svg v-else-if="item.icon === 'Monitor'" viewBox="0 0 24 24" width="18" height="18"><rect x="2" y="3" width="20" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" fill="none"/></svg>
            <svg v-else-if="item.icon === 'Warning'" viewBox="0 0 24 24" width="18" height="18"><path d="M12 2L1 21h22L12 2zm0 4.5l7.5 12h-15l7.5-12z" fill="currentColor"/><circle cx="12" cy="16" r="1.5" fill="var(--color-bg-secondary)"/><rect x="11" y="9" width="2" height="5" rx="0.5" fill="var(--color-bg-secondary)"/></svg>
            <svg v-else-if="item.icon === 'Document'" viewBox="0 0 24 24" width="18" height="18"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 2v6h6" fill="none" stroke="currentColor" stroke-width="2"/><line x1="8" y1="13" x2="16" y2="13" stroke="currentColor" stroke-width="2"/><line x1="8" y1="17" x2="16" y2="17" stroke="currentColor" stroke-width="2"/></svg>
            <svg v-else-if="item.icon === 'Folder'" viewBox="0 0 24 24" width="18" height="18"><path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 9h18" stroke="currentColor" stroke-width="2"/></svg>
            <svg v-else-if="item.icon === 'Share'" viewBox="0 0 24 24" width="18" height="18"><circle cx="6" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="6" r="3" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="18" r="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="m8.6 10.5 6.8-3M8.6 13.5l6.8 3" fill="none" stroke="currentColor" stroke-width="2"/></svg>
            <svg v-else-if="item.icon === 'ChatDotRound'" viewBox="0 0 24 24" width="18" height="18"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="10" r="1.5" fill="currentColor"/></svg>
          </el-icon>
            <span>{{ item.label }}</span>
            <span class="nav-code mono">{{ item.code }}</span>
          </button>
        </template>
      </nav>
      <div class="sidebar-footer">
        <span><i class="service-dot" />服务状态正常</span>
        <span class="mono">BUILD 1.0.0 · LOCAL</span>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="topbar">
        <span>工作台 <b>/</b> {{ pageTitle }}</span>
        <span class="topbar-meta mono">LOCAL MAINTENANCE CONSOLE</span>
      </header>
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
  width: 238px;
  min-width: 238px;
  background: var(--ui-sidebar);
  border-right: 1px solid var(--ui-border);
  display: flex;
  flex-direction: column;
  user-select: none;
}

.sidebar-brand {
  padding: 22px 20px 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--color-border);
}

.brand-icon {
  flex-shrink: 0;
}

.brand-text h1 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--ui-text);
  line-height: 1.3;
}

.brand-text span {
  display: block;
  margin-top: 2px;
  font: 10px var(--font-mono);
  color: var(--ui-text-quiet);
  letter-spacing: .06em;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-caption { margin: 10px 10px 4px; color: var(--ui-text-quiet); font: 10px var(--font-mono); letter-spacing: .08em; }
.nav-item {
  width: 100%;
  border: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 2px;
  background: transparent;
  color: var(--ui-text-muted);
  cursor: pointer;
  transition: background .16s ease, color .16s ease;
  font-size: 14px;
}

.nav-item:hover {
  background: var(--ui-panel-raised);
  color: var(--ui-text);
}

.nav-item.active {
  background: #1d2928;
  box-shadow: inset 2px 0 0 var(--ui-accent);
  color: var(--ui-accent-light);
  font-weight: 500;
}
.nav-code { margin-left: auto; color: var(--ui-text-quiet); font-size: 10px; }

.sidebar-footer {
  display: grid;
  gap: 5px;
  padding: 14px 20px;
  border-top: 1px solid var(--ui-border);
  font-size: 11px;
  color: var(--ui-text-muted);
}
.sidebar-footer .mono { color: var(--ui-text-quiet); font-size: 10px; }
.service-dot { display: inline-block; width: 6px; height: 6px; margin-right: 7px; border-radius: 50%; background: var(--ui-success); }

/* 主内容区 */
.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}
.topbar { position: sticky; top: 0; z-index: 5; display: flex; align-items: center; justify-content: space-between; height: 62px; padding: 0 32px; background: color-mix(in srgb, var(--ui-bg) 94%, transparent); border-bottom: 1px solid var(--ui-border); color: var(--ui-text-muted); font-size: 13px; backdrop-filter: blur(8px); }
.topbar b { padding: 0 7px; color: var(--ui-text-quiet); font-weight: 400; }
.topbar-meta { color: var(--ui-text-quiet); font-size: 10px; }

@media (max-width: 760px) {
  .app-layout { display: block; height: auto; overflow: visible; }
  .sidebar { width: 100%; min-width: 0; border-right: 0; border-bottom: 1px solid var(--ui-border); }
  .sidebar-brand, .sidebar-footer { display: none; }
  .sidebar-nav { flex-direction: row; gap: 4px; overflow-x: auto; padding: 8px 12px; }
  .nav-caption, .nav-code { display: none; }
  .nav-item { width: auto; flex: 0 0 auto; padding: 8px 10px; white-space: nowrap; }
  .main-content { overflow: visible; }
  .topbar { height: 52px; padding: 0 20px; }
  .topbar-meta { display: none; }
}
</style>
