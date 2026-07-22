/**
 * 前端 API 适配层。
 *
 * Mock 数据与后端接口的字段命名不同，因此在这里集中完成协议转换，避免页面组件感知后端细节。
 */
import { delay, del, get, isMockEnabled, patch, post, upload } from './client'
import type {
  DashboardSummary,
  Device,
  DeviceDetail,
  DeviceFormData,
  DeviceStatusRecord,
  ExternalMaterial,
  HistoricalFault,
  MaintenanceDraft,
  PaginatedResponse,
  Problem,
  ProblemFormData,
  RelatedDraft,
  WorkflowRun,
  MaterialType,
} from '../types'
import {
  getMockDeviceDetail,
  mockDashboardSummary,
  mockDevices,
  mockDrafts,
  mockProblems,
  mockWorkflows,
  nextId,
} from '../mock/data'

export { isMockEnabled }

interface BackendDevice {
  id: number
  code: string
  name: string
  model: string
  location: string
  status: string
  rated_pressure: number | null
  rated_power: number | null
  commissioned_at: string | null
  updated_at: string
}

interface BackendDeviceStatus {
  id: number
  device_id: number
  run_state: string
  pressure: number | null
  temperature: number | null
  vibration: number | null
  oil_level: string | null
  collected_at: string
  source: string
}

interface BackendProblem {
  id: number
  device_id: number
  symptom: string
  description: string | null
  severity: string
  status: string
  detected_at: string | null
  source: string
  draft_id: number | null
  created_at: string
}

interface BackendEvidence {
  source_type: string
  source_id: string | null
  title: string
  reference: string | null
  excerpt: string | null
  confidence: number | null
}

interface BackendDraft {
  id: number
  device_id: number
  problem_id: number | null
  diagnosis: string | null
  possible_causes: string[]
  inspection_steps: string[]
  repair_steps: string[]
  required_tools: string[]
  required_parts: string[]
  safety_notices: string[]
  evidence: BackendEvidence[]
  status: string
  requires_human_confirmation: boolean
  workflow_run_id: number | null
  source: string
  created_at: string
}

interface BackendWorkflowStep {
  id: number
  run_id: number
  step_order: number
  step_name: string
  tool_name: string | null
  status: string
  input_summary: string | null
  output_summary: string | null
  evidence: BackendEvidence[]
  error_message: string | null
  started_at: string
  finished_at: string | null
}

interface BackendWorkflow {
  id: number
  user_question: string
  device_id: number | null
  status: string
  started_at: string
  finished_at: string | null
  error_message: string | null
  draft_id: number | null
  steps: BackendWorkflowStep[]
}

interface BackendDashboardSummary {
  device_count: number
  active_device_count: number
  maintenance_device_count: number
  fault_device_count: number
  problem_count: number
  draft_count: number
  latest_workflow_id: number | null
}

interface BackendMaterial {
  id: number
  filename: string
  material_type: string
  source_description: string
  device_id: number | null
  device_model: string | null
  content_path: string | null
  content: string | null
  is_reference_allowed: boolean
  created_at: string
  updated_at: string
}

function queryString(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const result = query.toString()
  return result ? `?${result}` : ''
}

function paginate<T>(items: T[], page = 1, pageSize = 10): PaginatedResponse<T> {
  const start = (page - 1) * pageSize
  return { items: items.slice(start, start + pageSize), total: items.length, page, page_size: pageSize }
}

function deviceStatusToUi(status: string): Device['status'] {
  if (status === 'maintenance') return 'warning'
  if (status === 'fault' || status === 'offline' || status === 'archived') return 'fault'
  return 'normal'
}

function deviceStatusToBackend(status: string | undefined): string | undefined {
  if (status === undefined) return undefined
  if (status === 'normal') return 'active'
  if (status === 'warning') return 'maintenance'
  return 'fault'
}

function runStateToUi(state: string): string {
  return {
    running: '运行中',
    stopped: '停止',
    standby: '待机',
    fault: '故障停机',
  }[state] ?? state
}

function problemStatusToUi(status: string): Problem['status'] {
  const statuses: Record<string, Problem['status']> = {
    open: 'pending',
    investigating: 'repairing',
    resolved: 'resolved',
    archived: 'archived',
  }
  return statuses[status] ?? 'pending'
}

function problemStatusToBackend(status: string | undefined): string | undefined {
  if (status === undefined) return undefined
  return { pending: 'open', repairing: 'investigating' }[status] ?? status
}

function draftStatusToUi(status: string): MaintenanceDraft['status'] {
  return status === 'confirmed' ? 'confirmed' : status === 'archived' ? 'archived' : 'pending_review'
}

function draftStatusToBackend(status: string): string {
  return status === 'pending_review' ? 'pending_confirmation' : status
}

function workflowStatusToUi(status: string): WorkflowRun['status'] {
  if (status === 'completed') return 'completed'
  if (status === 'failed') return 'failed'
  return 'running'
}

function stepStatusToUi(status: string): 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped' {
  if (status === 'running') return 'in_progress'
  if (status === 'completed' || status === 'failed' || status === 'skipped') return status
  return 'pending'
}

function evidenceType(sourceType: string): 'case' | 'sop' | 'safety' | 'material' {
  if (sourceType.includes('case')) return 'case'
  if (sourceType.includes('sop')) return 'sop'
  if (sourceType.includes('safety')) return 'safety'
  return 'material'
}

function toDeviceStatus(raw: BackendDeviceStatus): DeviceStatusRecord {
  return {
    id: String(raw.id),
    device_id: String(raw.device_id),
    running_status: runStateToUi(raw.run_state),
    exhaust_pressure: raw.pressure ?? 0,
    temperature: raw.temperature ?? 0,
    vibration: raw.vibration ?? 0,
    oil_level: raw.oil_level ?? '-',
    collected_at: raw.collected_at,
    source: raw.source,
  }
}

function toDevice(raw: BackendDevice, latestStatus?: BackendDeviceStatus): Device {
  const indicator = latestStatus ? toDeviceStatus(latestStatus) : undefined
  return {
    id: String(raw.id),
    name: raw.name,
    model: raw.model,
    area: raw.location,
    status: deviceStatusToUi(raw.status),
    updated_at: raw.updated_at,
    rated_pressure: raw.rated_pressure ?? 0,
    rated_power: raw.rated_power ?? 0,
    commissioned_at: raw.commissioned_at ?? '',
    running_indicators: indicator,
  }
}

function toProblem(raw: BackendProblem, deviceName?: string): Problem {
  return {
    id: String(raw.id),
    device_id: String(raw.device_id),
    device_name: deviceName,
    symptom: raw.symptom,
    severity: raw.severity as Problem['severity'],
    status: problemStatusToUi(raw.status),
    discovered_at: raw.detected_at ?? raw.created_at,
    description: raw.description ?? '',
    possible_causes: [],
    source: raw.source,
    draft_id: raw.draft_id === null ? undefined : String(raw.draft_id),
  }
}

function toEvidence(raw: BackendEvidence) {
  return {
    type: evidenceType(raw.source_type),
    id: raw.source_id ?? raw.title,
    label: raw.title,
    relationship: raw.reference ?? '参考资料',
  }
}

function toDraft(raw: BackendDraft, deviceName?: string): MaintenanceDraft {
  return {
    id: String(raw.id),
    device_id: String(raw.device_id),
    device_name: deviceName,
    problem_id: raw.problem_id === null ? undefined : String(raw.problem_id),
    fault_diagnosis: raw.diagnosis ?? '尚未形成明确故障判断',
    possible_causes: raw.possible_causes,
    check_steps: raw.inspection_steps,
    repair_steps: raw.repair_steps,
    tools_and_parts: [...raw.required_tools, ...raw.required_parts],
    safety_notices: raw.safety_notices,
    evidence_refs: raw.evidence.map(toEvidence),
    generated_at: raw.created_at,
    workflow_run_id: raw.workflow_run_id === null ? undefined : String(raw.workflow_run_id),
    status: draftStatusToUi(raw.status),
    needs_confirmation: raw.requires_human_confirmation,
    risk_level: raw.safety_notices.length > 0 ? 'high' : 'medium',
  }
}

function toWorkflow(raw: BackendWorkflow, deviceName?: string): WorkflowRun {
  return {
    id: String(raw.id),
    user_question: raw.user_question,
    device_id: raw.device_id === null ? undefined : String(raw.device_id),
    device_name: deviceName,
    started_at: raw.started_at,
    finished_at: raw.finished_at ?? undefined,
    status: workflowStatusToUi(raw.status),
    draft_id: raw.draft_id === null ? undefined : String(raw.draft_id),
    steps: raw.steps.map((step) => ({
      id: String(step.id),
      run_id: String(step.run_id),
      step_name: step.step_name,
      step_status: stepStatusToUi(step.status),
      started_at: step.started_at,
      finished_at: step.finished_at ?? undefined,
      tool_name: step.tool_name ?? undefined,
      tool_input_summary: step.input_summary ?? undefined,
      tool_output_summary: step.output_summary ?? undefined,
      evidence_used: step.evidence.map((item) => item.title),
      error_info: step.error_message ?? undefined,
    })),
  }
}

function toMaterial(raw: BackendMaterial): ExternalMaterial {
  return {
    id: String(raw.id),
    filename: raw.filename,
    material_type: raw.material_type as MaterialType,
    source_description: raw.source_description,
    device_id: raw.device_id === null ? undefined : String(raw.device_id),
    device_model: raw.device_model ?? undefined,
    content_path: raw.content_path ?? undefined,
    content: raw.content ?? undefined,
    is_reference_allowed: raw.is_reference_allowed,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  }
}

async function fetchBackendDevices(params?: Record<string, string | number | undefined>) {
  return get<BackendDevice[]>(`/api/devices${queryString(params ?? {})}`)
}

async function fetchBackendDeviceNames(): Promise<Map<string, string>> {
  const devices = await fetchBackendDevices()
  return new Map(devices.map((device) => [String(device.id), device.name]))
}

async function fetchLatestStatus(deviceId: number): Promise<BackendDeviceStatus | undefined> {
  const statuses = await get<BackendDeviceStatus[]>(`/api/devices/${deviceId}/statuses?limit=1`)
  return statuses[0]
}

function devicePayload(data: Partial<DeviceFormData>, partial = false): Record<string, unknown> {
  const payload: Record<string, unknown> = {}
  if (!partial || data.name !== undefined) payload.name = data.name
  if (!partial || data.model !== undefined) payload.model = data.model
  if (!partial || data.area !== undefined) payload.location = data.area
  if (!partial || data.status !== undefined) payload.status = deviceStatusToBackend(data.status)
  if (!partial || data.rated_pressure !== undefined) payload.rated_pressure = data.rated_pressure
  if (!partial || data.rated_power !== undefined) payload.rated_power = data.rated_power
  if (!partial || data.commissioned_at !== undefined) {
    payload.commissioned_at = data.commissioned_at ? `${data.commissioned_at}T00:00:00` : null
  }
  if (!partial) {
    // 前端表单暂不要求用户填写编号，Demo 中自动生成稳定格式的编号。
    payload.code = `DEMO-${Date.now()}`
    payload.source = 'frontend'
  }
  return payload
}

function problemPayload(data: Partial<ProblemFormData>): Record<string, unknown> {
  const payload: Record<string, unknown> = {}
  if (data.device_id !== undefined) payload.device_id = Number(data.device_id)
  if (data.symptom !== undefined) payload.symptom = data.symptom
  if (data.description !== undefined) payload.description = data.description
  if (data.severity !== undefined) payload.severity = data.severity
  if (data.status !== undefined) payload.status = problemStatusToBackend(data.status)
  if (data.source !== undefined) payload.source = data.source
  return payload
}

// ===================== 总览 =====================

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  if (isMockEnabled()) {
    await delay(400)
    return { ...mockDashboardSummary }
  }
  const summary = await get<BackendDashboardSummary>('/api/dashboard/summary')
  const recent = await fetchDrafts({ page: 1, page_size: 5 })
  const latestWorkflow = summary.latest_workflow_id === null
    ? undefined
    : await fetchWorkflowDetail(String(summary.latest_workflow_id))
  return {
    total_devices: summary.device_count,
    normal_count: summary.active_device_count,
    warning_count: summary.maintenance_device_count,
    fault_count: summary.fault_device_count,
    pending_problems: summary.problem_count,
    recent_drafts: recent.items,
    device_status_distribution: [
      { name: '正常', value: summary.active_device_count },
      { name: '预警', value: summary.maintenance_device_count },
      { name: '故障', value: summary.fault_device_count },
    ],
    latest_workflow: latestWorkflow,
  }
}

// ===================== 设备 =====================

export async function fetchDevices(params?: {
  search?: string
  status?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<Device>> {
  if (isMockEnabled()) {
    await delay(300)
    let list = [...mockDevices]
    if (params?.search) {
      const kw = params.search.toLowerCase()
      list = list.filter((d) => d.name.toLowerCase().includes(kw) || d.id.toLowerCase().includes(kw))
    }
    if (params?.status) list = list.filter((d) => d.status === params.status)
    return paginate(list, params?.page, params?.page_size)
  }
  const rawDevices = await fetchBackendDevices({
    keyword: params?.search,
    status: deviceStatusToBackend(params?.status),
  })
  const devices = await Promise.all(
    rawDevices.map(async (device) => toDevice(device, await fetchLatestStatus(device.id)))
  )
  return paginate(devices, params?.page, params?.page_size)
}

export async function fetchDeviceDetail(deviceId: string): Promise<DeviceDetail> {
  if (isMockEnabled()) {
    await delay(350)
    const detail = getMockDeviceDetail(deviceId)
    if (!detail) throw new Error('设备不存在')
    return detail
  }
  const raw = await get<BackendDevice>(`/api/devices/${Number(deviceId)}`)
  const [rawStatuses, problems, drafts] = await Promise.all([
    get<BackendDeviceStatus[]>(`/api/devices/${raw.id}/statuses?limit=50`),
    fetchProblems({ device_id: String(raw.id), page_size: 50 }),
    fetchDrafts({ device_id: String(raw.id), page_size: 50 }),
  ])
  return {
    ...toDevice(raw, rawStatuses[0]),
    status_history: rawStatuses.map(toDeviceStatus),
    historical_faults: problems.items.map<HistoricalFault>((problem) => ({
      id: problem.id,
      symptom: problem.symptom,
      severity: problem.severity,
      discovered_at: problem.discovered_at,
      status: problem.status,
      description: problem.description,
    })),
    related_components: [],
    related_cases: [],
    related_drafts: drafts.items.map<RelatedDraft>((draft) => ({
      id: draft.id,
      fault_diagnosis: draft.fault_diagnosis,
      status: draft.status,
      generated_at: draft.generated_at,
    })),
  }
}

export async function createDevice(data: DeviceFormData): Promise<Device> {
  if (isMockEnabled()) {
    await delay(400)
    const device: Device = { id: nextId('dev'), ...data, updated_at: new Date().toISOString() }
    mockDevices.push(device)
    return device
  }
  const raw = await post<BackendDevice>('/api/devices', devicePayload(data))
  return toDevice(raw)
}

export async function updateDevice(deviceId: string, data: Partial<DeviceFormData>): Promise<Device> {
  if (isMockEnabled()) {
    await delay(350)
    const idx = mockDevices.findIndex((d) => d.id === deviceId)
    if (idx === -1) throw new Error('设备不存在')
    mockDevices[idx] = { ...mockDevices[idx], ...data, updated_at: new Date().toISOString() }
    return mockDevices[idx]
  }
  const raw = await patch<BackendDevice>(`/api/devices/${Number(deviceId)}`, devicePayload(data, true))
  return toDevice(raw)
}

export async function archiveDevice(deviceId: string): Promise<Device> {
  if (isMockEnabled()) {
    await delay(300)
    const idx = mockDevices.findIndex((d) => d.id === deviceId)
    if (idx === -1) throw new Error('设备不存在')
    mockDevices[idx] = { ...mockDevices[idx], status: 'fault', updated_at: new Date().toISOString() }
    return mockDevices[idx]
  }
  const raw = await del<BackendDevice>(`/api/devices/${Number(deviceId)}`)
  return toDevice(raw)
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
  if (isMockEnabled()) {
    await delay(300)
    let list = [...mockProblems]
    if (params?.search) list = list.filter((p) => p.symptom.toLowerCase().includes(params.search!.toLowerCase()))
    if (params?.severity) list = list.filter((p) => p.severity === params.severity)
    if (params?.status) list = list.filter((p) => p.status === params.status)
    if (params?.device_id) list = list.filter((p) => p.device_id === params.device_id)
    return paginate(list, params?.page, params?.page_size)
  }
  const rawProblems = await get<BackendProblem[]>(`/api/problems${queryString({
    keyword: params?.search,
    severity: params?.severity,
    status: problemStatusToBackend(params?.status),
    device_id: params?.device_id ? Number(params.device_id) : undefined,
  })}`)
  const names = await fetchBackendDeviceNames()
  return paginate(rawProblems.map((problem) => toProblem(problem, names.get(String(problem.device_id)))), params?.page, params?.page_size)
}

export async function fetchProblemDetail(problemId: string): Promise<Problem> {
  if (isMockEnabled()) {
    await delay(300)
    const problem = mockProblems.find((item) => item.id === problemId)
    if (!problem) throw new Error('问题不存在')
    return problem
  }
  const raw = await get<BackendProblem>(`/api/problems/${Number(problemId)}`)
  const names = await fetchBackendDeviceNames()
  return toProblem(raw, names.get(String(raw.device_id)))
}

export async function createProblem(data: ProblemFormData): Promise<Problem> {
  if (isMockEnabled()) {
    await delay(400)
    const device = mockDevices.find((item) => item.id === data.device_id)
    const problem: Problem = { id: nextId('prob'), ...data, device_name: device?.name, discovered_at: new Date().toISOString() }
    mockProblems.unshift(problem)
    return problem
  }
  const raw = await post<BackendProblem>('/api/problems', problemPayload(data))
  const names = await fetchBackendDeviceNames()
  return toProblem(raw, names.get(String(raw.device_id)))
}

export async function updateProblem(problemId: string, data: Partial<ProblemFormData>): Promise<Problem> {
  if (isMockEnabled()) {
    await delay(350)
    const idx = mockProblems.findIndex((p) => p.id === problemId)
    if (idx === -1) throw new Error('问题不存在')
    mockProblems[idx] = { ...mockProblems[idx], ...data }
    return mockProblems[idx]
  }
  const raw = await patch<BackendProblem>(`/api/problems/${Number(problemId)}`, problemPayload(data))
  const names = await fetchBackendDeviceNames()
  return toProblem(raw, names.get(String(raw.device_id)))
}

export async function archiveProblem(problemId: string): Promise<Problem> {
  if (isMockEnabled()) {
    await delay(300)
    const idx = mockProblems.findIndex((p) => p.id === problemId)
    if (idx === -1) throw new Error('问题不存在')
    mockProblems[idx] = { ...mockProblems[idx], status: 'archived' }
    return mockProblems[idx]
  }
  const raw = await del<BackendProblem>(`/api/problems/${Number(problemId)}`)
  const names = await fetchBackendDeviceNames()
  return toProblem(raw, names.get(String(raw.device_id)))
}

// ===================== 维修草案 =====================

export async function fetchDrafts(params?: {
  device_id?: string
  status?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<MaintenanceDraft>> {
  if (isMockEnabled()) {
    await delay(300)
    let list = [...mockDrafts]
    if (params?.device_id) list = list.filter((draft) => draft.device_id === params.device_id)
    if (params?.status) list = list.filter((draft) => draft.status === params.status)
    if (params?.search) list = list.filter((draft) => draft.fault_diagnosis.toLowerCase().includes(params.search!.toLowerCase()) || draft.id.includes(params.search!))
    return paginate(list, params?.page, params?.page_size)
  }
  const rawDrafts = await get<BackendDraft[]>(`/api/drafts${queryString({
    device_id: params?.device_id ? Number(params.device_id) : undefined,
    status: params?.status ? draftStatusToBackend(params.status) : undefined,
  })}`)
  const names = await fetchBackendDeviceNames()
  let drafts = rawDrafts.map((draft) => toDraft(draft, names.get(String(draft.device_id))))
  if (params?.search) {
    const keyword = params.search.toLowerCase()
    drafts = drafts.filter((draft) => draft.id.includes(params.search!) || draft.fault_diagnosis.toLowerCase().includes(keyword))
  }
  return paginate(drafts, params?.page, params?.page_size)
}

export async function fetchDraftDetail(draftId: string): Promise<MaintenanceDraft> {
  if (isMockEnabled()) {
    await delay(300)
    const draft = mockDrafts.find((item) => item.id === draftId)
    if (!draft) throw new Error('草案不存在')
    return draft
  }
  const raw = await get<BackendDraft>(`/api/drafts/${Number(draftId)}`)
  const names = await fetchBackendDeviceNames()
  return toDraft(raw, names.get(String(raw.device_id)))
}

export async function updateDraftStatus(draftId: string, status: string): Promise<MaintenanceDraft> {
  if (isMockEnabled()) {
    await delay(300)
    const idx = mockDrafts.findIndex((draft) => draft.id === draftId)
    if (idx === -1) throw new Error('草案不存在')
    mockDrafts[idx] = { ...mockDrafts[idx], status: status as MaintenanceDraft['status'] }
    return mockDrafts[idx]
  }
  const raw = await patch<BackendDraft>(`/api/drafts/${Number(draftId)}/status`, { status: draftStatusToBackend(status) })
  const names = await fetchBackendDeviceNames()
  return toDraft(raw, names.get(String(raw.device_id)))
}

// ===================== 工作流 =====================

export async function fetchWorkflowDetail(runId: string): Promise<WorkflowRun> {
  if (isMockEnabled()) {
    await delay(400)
    const workflow = mockWorkflows.find((item) => item.id === runId)
    if (!workflow) throw new Error('工作流不存在')
    return workflow
  }
  const raw = await get<BackendWorkflow>(`/api/workflows/${Number(runId)}`)
  const names = raw.device_id === null ? new Map<string, string>() : await fetchBackendDeviceNames()
  return toWorkflow(raw, raw.device_id === null ? undefined : names.get(String(raw.device_id)))
}

// ===================== 外部资料 =====================

export async function fetchMaterials(params?: {
  device_id?: string
  material_type?: string
  reference_allowed_only?: boolean
}): Promise<ExternalMaterial[]> {
  if (isMockEnabled()) {
    await delay(250)
    return []
  }
  const raw = await get<BackendMaterial[]>(`/api/materials${queryString({
    device_id: params?.device_id ? Number(params.device_id) : undefined,
    material_type: params?.material_type,
    reference_allowed_only: params?.reference_allowed_only ? 'true' : undefined,
  })}`)
  return raw.map(toMaterial)
}

export async function importMaterial(data: {
  file: File
  source_description: string
  device_id?: string
  device_model?: string
  is_reference_allowed: boolean
}): Promise<ExternalMaterial> {
  if (isMockEnabled()) {
    await delay(350)
    return {
      id: `mock-material-${Date.now()}`,
      filename: data.file.name,
      material_type: 'external_reference',
      source_description: data.source_description,
      device_id: data.device_id,
      device_model: data.device_model,
      is_reference_allowed: data.is_reference_allowed,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  }
  const form = new FormData()
  form.append('file', data.file)
  form.append('source_description', data.source_description)
  if (data.device_id) form.append('device_id', data.device_id)
  if (data.device_model) form.append('device_model', data.device_model)
  form.append('is_reference_allowed', String(data.is_reference_allowed))
  return toMaterial(await upload<BackendMaterial>('/api/materials/import', form))
}

export async function deleteMaterial(materialId: string): Promise<void> {
  if (isMockEnabled()) {
    await delay(250)
    return
  }
  await del<void>(`/api/materials/${Number(materialId)}`)
}

// ===================== 健康检查 =====================

export async function checkHealth(): Promise<boolean> {
  try {
    if (isMockEnabled()) {
      await delay(200)
      return true
    }
    await get('/api/health')
    return true
  } catch {
    return false
  }
}

/** 直接检查 Hermes API 健康端点，避免把维护服务状态误当成 Agent 状态。 */
export async function checkHermesHealth(): Promise<boolean> {
  const url = import.meta.env.VITE_HERMES_API_HEALTH_URL || 'http://127.0.0.1:8642/health'
  try {
    const response = await fetch(url)
    return response.ok
  } catch {
    return false
  }
}
