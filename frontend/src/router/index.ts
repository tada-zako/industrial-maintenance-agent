/**
 * Vue Router 配置 -- 运维看板路由
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/overview',
  },
  {
    path: '/overview',
    name: 'Overview',
    component: () => import('../views/Overview.vue'),
    meta: { title: '运维总览' },
  },
  {
    path: '/devices',
    name: 'DeviceList',
    component: () => import('../views/DeviceList.vue'),
    meta: { title: '设备管理' },
  },
  {
    path: '/devices/:deviceId',
    name: 'DeviceDetail',
    component: () => import('../views/DeviceDetail.vue'),
    meta: { title: '设备详情' },
  },
  {
    path: '/problems',
    name: 'ProblemList',
    component: () => import('../views/ProblemList.vue'),
    meta: { title: '问题中心' },
  },
  {
    path: '/drafts',
    name: 'DraftList',
    component: () => import('../views/DraftList.vue'),
    meta: { title: '维修草案' },
  },
  {
    path: '/drafts/:draftId',
    name: 'DraftDetail',
    component: () => import('../views/DraftDetail.vue'),
    meta: { title: '草案详情' },
  },
  {
    path: '/materials',
    name: 'MaterialList',
    component: () => import('../views/MaterialList.vue'),
    meta: { title: '运维资料' },
  },
  {
    path: '/workflows/:runId',
    name: 'WorkflowDetail',
    component: () => import('../views/WorkflowDetail.vue'),
    meta: { title: '工作流详情' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/Chat.vue'),
    meta: { title: 'Hermes 助手' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/overview',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 更新页面标题
router.afterEach((to) => {
  const title = to.meta?.title
  document.title = title ? `${title} - 工业运维 Agent` : '工业运维 Agent 看板'
})

export default router
