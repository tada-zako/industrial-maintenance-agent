/**
 * API 接口层 -- 封装所有后端 API 调用，支持 Mock 回退
 */
import { delay } from './client'
import type {
  DashboardSummary,
  Device,
  DeviceDetail,
  Problem,
  MaintenanceDraft,
  WorkflowRun,
  DeviceFormData,
  ProblemFormData,
  PaginatedResponse,
} from '../types'
import {
  mockDashboardSummary,
  mockDevices,
  mockProblems,
  mockDrafts,
  mockWorkflows,
  getMockDeviceDetail,
  nextId,
} from '../mock/data'

/** 是否启用 Mock 模式 */
export function isMockEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.DEV
}

// ===================== 总览 =====================

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    return get<DashboardSummary>('/api/dashboard/summary')
  }
  await delay(400)
  return { ...mockDashboardSummary }
}

// ===================== 设备 =====================

export async function fetchDevices(params?: {
  search?: string
  status?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<Device>> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    const qs = params ? '?' + new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null) as [string, string][]
    ).toString() : ''
    return get<PaginatedResponse<Device>>('/api/devices' + qs)
  }
  await delay(300)
  let list = [...mockDevices]
  if (params?.search) {
    const kw = params.search.toLowerCase()
    list = list.filter(
      (d) => d.name.toLowerCase().includes(kw) || d.id.toLowerCase().includes(kw)
    )
  }
  if (params?.status) {
    list = list.filter((d) => d.status === params.status)
  }
  const page = params?.page || 1
  const pageSize = params?.page_size || 10
  const start = (page - 1) * pageSize
  return { items: list.slice(start, start + pageSize), total: list.length, page, page_size: pageSize }
}

export async function fetchDeviceDetail(deviceId: string): Promise<DeviceDetail> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    return get<DeviceDetail>(`/api/devices/${deviceId}`)
  }
  await delay(350)
  const detail = getMockDeviceDetail(deviceId)
  if (!detail) throw new Error('设备不存在')
  return detail
}

/** 创建设备（Mock 模式追加到列表） */
export async function createDevice(data: DeviceFormData): Promise<Device> {
  if (!isMockEnabled()) {
    const { post } = await import('./client')
    return post<Device>('/api/devices', data)
  }
  await delay(400)
  const device: Device = {
    id: nextId('dev'),
    ...data,
    updated_at: new Date().toISOString(),
  }
  mockDevices.push(device)
  return device
}

/** 更新设备 */
export async function updateDevice(
  deviceId: string,
  data: Partial<DeviceFormData>
): Promise<Device> {
  if (!isMockEnabled()) {
    const { patch } = await import('./client')
    return patch<Device>(`/api/devices/${deviceId}`, data)
  }
  await delay(350)
  const idx = mockDevices.findIndex((d) => d.id === deviceId)
  if (idx === -1) throw new Error('设备不存在')
  mockDevices[idx] = {
    ...mockDevices[idx],
    ...data,
    updated_at: new Date().toISOString(),
  }
  return mockDevices[idx]
}

/** 归档（停用）设备 */
export async function archiveDevice(deviceId: string): Promise<Device> {
  if (!isMockEnabled()) {
    const { del } = await import('./client')
    return del<Device>(`/api/devices/${deviceId}`)
  }
  await delay(300)
  const idx = mockDevices.findIndex((d) => d.id === deviceId)
  if (idx === -1) throw new Error('设备不存在')
  mockDevices[idx] = { ...mockDevices[idx], status: 'fault', updated_at: new Date().toISOString() }
  return mockDevices[idx]
}

// ===================== 问题 =====================

export async function fetchProblems(params?: {
  search?: string
  severity?: string
  status?: string
  device_id?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<Problem>> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    const qs = params ? '?' + new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null) as [string, string][]
    ).toString() : ''
    return get<PaginatedResponse<Problem>>('/api/problems' + qs)
  }
  await delay(300)
  let list = [...mockProblems]
  if (params?.search) {
    const kw = params.search.toLowerCase()
    list = list.filter((p) => p.symptom.toLowerCase().includes(kw))
  }
  if (params?.severity) list = list.filter((p) => p.severity === params.severity)
  if (params?.status) list = list.filter((p) => p.status === params.status)
  if (params?.device_id) list = list.filter((p) => p.device_id === params.device_id)
  const page = params?.page || 1
  const pageSize = params?.page_size || 10
  const start = (page - 1) * pageSize
  return { items: list.slice(start, start + pageSize), total: list.length, page, page_size: pageSize }
}

export async function fetchProblemDetail(problemId: string): Promise<Problem> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    return get<Problem>(`/api/problems/${problemId}`)
  }
  await delay(300)
  const p = mockProblems.find((x) => x.id === problemId)
  if (!p) throw new Error('问题不存在')
  return p
}

export async function createProblem(data: ProblemFormData): Promise<Problem> {
  if (!isMockEnabled()) {
    const { post } = await import('./client')
    return post<Problem>('/api/problems', data)
  }
  await delay(400)
  const device = mockDevices.find((d) => d.id === data.device_id)
  const problem: Problem = {
    id: nextId('prob'),
    ...data,
    device_name: device?.name,
    discovered_at: new Date().toISOString(),
  }
  mockProblems.unshift(problem)
  return problem
}

export async function updateProblem(
  problemId: string,
  data: Partial<ProblemFormData>
): Promise<Problem> {
  if (!isMockEnabled()) {
    const { patch } = await import('./client')
    return patch<Problem>(`/api/problems/${problemId}`, data)
  }
  await delay(350)
  const idx = mockProblems.findIndex((p) => p.id === problemId)
  if (idx === -1) throw new Error('问题不存在')
  mockProblems[idx] = { ...mockProblems[idx], ...data }
  return mockProblems[idx]
}

export async function archiveProblem(problemId: string): Promise<Problem> {
  if (!isMockEnabled()) {
    const { del } = await import('./client')
    return del<Problem>(`/api/problems/${problemId}`)
  }
  await delay(300)
  const idx = mockProblems.findIndex((p) => p.id === problemId)
  if (idx === -1) throw new Error('问题不存在')
  mockProblems[idx] = { ...mockProblems[idx], status: 'archived' }
  return mockProblems[idx]
}

// ===================== 维修草案 =====================

export async function fetchDrafts(params?: {
  device_id?: string
  status?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<MaintenanceDraft>> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    const qs = params ? '?' + new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null) as [string, string][]
    ).toString() : ''
    return get<PaginatedResponse<MaintenanceDraft>>('/api/drafts' + qs)
  }
  await delay(300)
  let list = [...mockDrafts]
  if (params?.device_id) list = list.filter((d) => d.device_id === params.device_id)
  if (params?.status) list = list.filter((d) => d.status === params.status)
  if (params?.search) {
    const kw = params.search.toLowerCase()
    list = list.filter(
      (d) => d.fault_diagnosis.toLowerCase().includes(kw) || d.id.toLowerCase().includes(kw)
    )
  }
  const page = params?.page || 1
  const pageSize = params?.page_size || 10
  const start = (page - 1) * pageSize
  return { items: list.slice(start, start + pageSize), total: list.length, page, page_size: pageSize }
}

export async function fetchDraftDetail(draftId: string): Promise<MaintenanceDraft> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    return get<MaintenanceDraft>(`/api/drafts/${draftId}`)
  }
  await delay(300)
  const d = mockDrafts.find((x) => x.id === draftId)
  if (!d) throw new Error('草案不存在')
  return d
}

export async function updateDraftStatus(
  draftId: string,
  status: string
): Promise<MaintenanceDraft> {
  if (!isMockEnabled()) {
    const { patch } = await import('./client')
    return patch<MaintenanceDraft>(`/api/drafts/${draftId}/status`, { status })
  }
  await delay(300)
  const idx = mockDrafts.findIndex((d) => d.id === draftId)
  if (idx === -1) throw new Error('草案不存在')
  mockDrafts[idx] = { ...mockDrafts[idx], status: status as MaintenanceDraft['status'] }
  return mockDrafts[idx]
}

// ===================== 工作流 =====================

export async function fetchWorkflowDetail(runId: string): Promise<WorkflowRun> {
  if (!isMockEnabled()) {
    const { get } = await import('./client')
    return get<WorkflowRun>(`/api/workflows/${runId}`)
  }
  await delay(400)
  const wf = mockWorkflows.find((w) => w.id === runId)
  if (!wf) throw new Error('工作流不存在')
  return wf
}

// ===================== 健康检查 =====================

export async function checkHealth(): Promise<boolean> {
  try {
    if (isMockEnabled()) {
      await delay(200)
      return true
    }
    const { get } = await import('./client')
    await get('/api/health')
    return true
  } catch {
    return false
  }
}
