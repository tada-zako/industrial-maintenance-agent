<script setup lang="ts">
/**
 * 应用级布局 -- 侧栏 + 顶栏 + 主内容区
 * 基于设计稿 design-prototype.html 重构
 */
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

/** 导航分组 */
const navGroups = [
  {
    caption: '工作台',
    items: [
      { path: '/overview', label: '运维总览', code: '01',
        icon: 'M4 20V10m8 10V4m8 16v-7' },
      { path: '/devices', label: '设备管理', code: '02',
        icon: 'rect:3,4,18,13|M9 21h6m-3-4v4' },
      { path: '/problems', label: '问题中心', code: '03',
        icon: 'M12 3 2.5 20h19L12 3Z|M12 9v5m0 3h.01' },
      { path: '/drafts', label: '维修草案', code: '04',
        icon: 'M6 3h9l4 4v14H6z|M15 3v5h5M9 13h6m-6 4h6' },
    ],
  },
  {
    caption: '资料与协作',
    items: [
      { path: '/materials', label: '运维资料', code: '05',
        icon: 'M3 7h7l2 2h9v10H3z' },
      { path: '/knowledge', label: '知识图谱', code: '06',
        icon: 'circle:6,12,2.4|circle:18,6,2.4|circle:18,18,2.4|M8.1 10.8l7.7-3.6m-7.7 6l7.7 3.6' },
      { path: '/chat', label: 'Hermes 助手', code: '07',
        icon: 'M20 15a3 3 0 0 1-3 3H8l-4 3V6a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v9Z' },
    ],
  },
]

function navigate(path: string) {
  router.push(path)
}

function isActive(path: string): boolean {
  if (path === '/overview') return route.path === '/overview'
  return route.path.startsWith(path)
}

/** 面包屑映射 */
const breadcrumbMap: Record<string, string> = {
  '/overview': '运维总览',
  '/devices': '设备管理',
  '/problems': '问题中心',
  '/drafts': '维修草案',
  '/materials': '运维资料',
  '/knowledge': '知识图谱',
  '/chat': 'Hermes 助手',
}

/** 当前页面路径文字 */
function currentPageLabel(): string {
  for (const [prefix, label] of Object.entries(breadcrumbMap)) {
    if (route.path.startsWith(prefix)) return label
  }
  return '概览'
}
</script>

<template>
  <div class="shell">
    <!-- ======== 侧边栏 ======== -->
    <aside class="sidebar">
      <!-- 品牌区 -->
      <div class="brand">
        <div class="brand-top">
          <div class="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="m12 3 7 4-7 4-7-4 7-4Z"/><path d="m5 13 7 4 7-4M5 17l7 4 7-4"/>
            </svg>
          </div>
          <span class="brand-title">工业运维 Agent</span>
        </div>
        <div class="brand-subtitle">maintenance console</div>
      </div>

      <!-- 导航分组 -->
      <nav class="nav" aria-label="主导航" v-for="group in navGroups" :key="group.caption">
        <span class="nav-caption">{{ group.caption }}</span>
        <button
          v-for="item in group.items"
          :key="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          @click="navigate(item.path)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
            <template v-if="item.icon.startsWith('rect:')">
              <rect :x="item.icon.split('|')[0].split(':')[1].split(',')[0]" :y="item.icon.split('|')[0].split(':')[1].split(',')[1]" :width="item.icon.split('|')[0].split(':')[1].split(',')[2]" :height="item.icon.split('|')[0].split(':')[1].split(',')[3]"/>
              <path v-if="item.icon.includes('|')" :d="item.icon.split('|')[1]"/>
            </template>
            <template v-else-if="item.icon.startsWith('circle:')">
              <circle v-for="(c, ci) in item.icon.split('|').filter(p => p.startsWith('circle:'))" :key="ci" :cx="c.split(':')[1].split(',')[0]" :cy="c.split(':')[1].split(',')[1]" :r="c.split(':')[1].split(',')[2]"/>
              <path v-if="item.icon.split('|').some(p => p.startsWith('M'))" :d="item.icon.split('|').find(p => p.startsWith('M'))"/>
            </template>
            <template v-else>
              <path :d="item.icon"/>
            </template>
          </svg>
          {{ item.label }}
          <span class="nav-code">{{ item.code }}</span>
        </button>
      </nav>

      <!-- 服务状态 -->
      <div class="rail-status">
        <div class="status-line"><i class="status-dot"></i>服务状态正常</div>
        <div class="build">BUILD 1.0.0 · LOCAL</div>
      </div>
    </aside>

    <!-- ======== 主内容区 ======== -->
    <div class="main">
      <!-- 顶栏 -->
      <header class="topbar">
        <div class="breadcrumb">
          工作台 <span> / </span> <b>{{ currentPageLabel() }}</b>
        </div>
        <div class="top-meta">
          <span>数据源：MOCK / SQLITE</span>
          <span class="dot">●</span>
          <span>LAST SYNC 10:32:18</span>
        </div>
      </header>

      <!-- 内容 -->
      <div class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* === 整体布局 === */
.shell {
  display: grid;
  grid-template-columns: 238px minmax(0, 1fr);
  min-height: 100vh;
}

/* === 侧边栏 === */
.sidebar {
  background: var(--ink);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  padding: 20px 12px 14px;
  user-select: none;
}

.brand {
  padding: 0 8px 22px;
  border-bottom: 1px solid var(--line);
}

.brand-top {
  display: flex;
  align-items: center;
  gap: 11px;
}

.brand-mark {
  width: 30px;
  height: 30px;
  border: 1px solid var(--cyan);
  display: grid;
  place-items: center;
  color: var(--cyan-light);
  flex-shrink: 0;
}

.brand-mark svg {
  width: 17px;
  height: 17px;
}

.brand-title {
  font-size: 15px;
  font-weight: 650;
  letter-spacing: 0.02em;
}

.brand-subtitle {
  margin: 4px 0 0 42px;
  color: var(--quiet);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

/* 导航 */
.nav {
  padding-top: 14px;
  display: grid;
  gap: 3px;
}

.nav-caption {
  color: var(--quiet);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  padding: 0 8px 7px;
  margin-top: 2px;
}

.nav-item {
  width: 100%;
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 39px;
  padding: 0 10px;
  text-align: left;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
  font-size: 13px;
}

.nav-item svg {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.nav-item:hover {
  background: #1e1e1e;
  color: var(--white);
}

.nav-item.active {
  border-left-color: var(--cyan);
  background: #1d2524;
  color: var(--white);
}

.nav-item.active .nav-code {
  color: var(--cyan-light);
}

.nav-code {
  color: var(--quiet);
  font: 10px var(--font-mono);
  margin-left: auto;
}

/* 服务状态 */
.rail-status {
  margin-top: auto;
  padding: 16px 8px 0;
  border-top: 1px solid var(--line);
}

.status-line {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-size: 12px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 0 3px rgba(101, 169, 132, 0.08);
}

.build {
  margin-top: 10px;
  color: var(--quiet);
  font: 10px var(--font-mono);
}

/* === 主区 === */
.main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* 顶栏 */
.topbar {
  height: 62px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--content-x);
  flex-shrink: 0;
}

.breadcrumb {
  color: var(--muted);
  font-size: 12px;
}

.breadcrumb span {
  color: var(--quiet);
}

.breadcrumb b {
  color: var(--white);
  font-weight: 500;
}

.top-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  color: var(--quiet);
  font: 11px var(--font-mono);
}

.top-meta .dot {
  color: var(--cyan);
}

/* 内容区填满剩余空间 */
.content-area {
  flex: 1;
  overflow-y: auto;
}

/* 响应式 */
@media (max-width: 760px) {
  .shell {
    display: block;
  }
  .sidebar {
    display: none;
  }
  .topbar {
    height: 52px;
  }
  .top-meta {
    display: none;
  }
}
</style>
