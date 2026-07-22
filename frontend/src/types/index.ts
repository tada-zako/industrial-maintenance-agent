/** 设备状态常量 */
export type DeviceStatus = 'normal' | 'warning' | 'fault'

/** 问题严重程度 */
export type ProblemSeverity = 'low' | 'medium' | 'high' | 'critical'

/** 问题处理状态 */
export type ProblemStatus = 'pending' | 'investigating' | 'repairing' | 'resolved' | 'archived'

/** 维修草案状态 */
export type DraftStatus = 'pending_review' | 'confirmed' | 'rejected' | 'archived'

/** 工作流运行状态 */
export type WorkflowStatus = 'running' | 'completed' | 'failed'

/** 外部运维资料类型 */
export type MaterialType = 'manual' | 'sop' | 'case' | 'external_reference' | 'other'

/** 步骤执行状态 */
export type StepStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped'

/** 设备基本信息 */
export interface Device {
  id: string
  name: string
  model: string
  area: string
  status: DeviceStatus
  updated_at: string
  rated_pressure: number
  rated_power: number
  commissioned_at: string
  /** 最近一次运行指标 */
  running_indicators?: RunningIndicators
}

/** 设备运行指标 */
export interface RunningIndicators {
  id: string
  device_id: string
  running_status: string
  exhaust_pressure: number
  temperature: number
  vibration: number
  oil_level: string
  collected_at: string
  source: string
}

/** 设备历史状态记录 */
export interface DeviceStatusRecord {
  id: string
  device_id: string
  running_status: string
  exhaust_pressure: number
  temperature: number
  vibration: number
  oil_level: string
  collected_at: string
  source: string
}

/** 历史故障 */
export interface HistoricalFault {
  id: string
  symptom: string
  severity: ProblemSeverity
  discovered_at: string
  status: ProblemStatus
  description: string
}

/** 关联部件 */
export interface RelatedComponent {
  id: string
  name: string
  type: string
}

/** 知识图谱关联案例 */
export interface RelatedCase {
  id: string
  title: string
  symptom: string
  resolution: string
}

/** 关联维修草案（简） */
export interface RelatedDraft {
  id: string
  fault_diagnosis: string
  status: DraftStatus
  generated_at: string
}

/** 问题 / 故障 */
export interface Problem {
  id: string
  device_id: string
  device_name?: string
  symptom: string
  severity: ProblemSeverity
  status: ProblemStatus
  discovered_at: string
  description: string
  possible_causes: string[]
  source: string
  draft_id?: string
}

/** 维修方案草案 */
export interface MaintenanceDraft {
  id: string
  device_id: string
  device_name?: string
  problem_id?: string
  fault_diagnosis: string
  possible_causes: string[]
  check_steps: string[]
  repair_steps: string[]
  tools_and_parts: string[]
  safety_notices: string[]
  evidence_refs: EvidenceRef[]
  generated_at: string
  workflow_run_id?: string
  status: DraftStatus
  needs_confirmation: boolean
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  review_feedback?: string
  reviewed_at?: string
}

/** 图谱节点与关系，字段与后端 Knowledge Schema 保持一致。 */
export interface KnowledgeNode {
  id: string
  type: string
  name: string
  source: string
  properties: Record<string, unknown>
}

export interface KnowledgeRelationship {
  source_id: string
  target_id: string
  type: string
}

export interface KnowledgeCase {
  id: string
  name: string
  device_model: string
  symptoms: string[]
  source: string
}

export interface KnowledgeGraphResult {
  nodes: KnowledgeNode[]
  relationships: KnowledgeRelationship[]
  matches: Array<{
    symptom: string
    causes: string[]
    actions: string[]
    sops: string[]
    safety_notices: string[]
  }>
  cases: KnowledgeCase[]
  evidence: EvidenceRef[]
}

/** 知识图谱证据引用 */
export interface EvidenceRef {
  type: 'case' | 'sop' | 'safety' | 'material'
  id: string
  label: string
  relationship: string
}

/** 外部资料元数据和可展示的文本内容 */
export interface ExternalMaterial {
  id: string
  filename: string
  material_type: MaterialType
  source_description: string
  device_id?: string
  device_model?: string
  content_path?: string
  content?: string
  is_reference_allowed: boolean
  created_at: string
  updated_at: string
}

/** 工作流运行记录 */
export interface WorkflowRun {
  id: string
  user_question: string
  device_id?: string
  device_name?: string
  started_at: string
  finished_at?: string
  status: WorkflowStatus
  draft_id?: string
  steps: WorkflowStep[]
}

/** 工作流步骤 */
export interface WorkflowStep {
  id: string
  run_id: string
  step_name: string
  step_status: StepStatus
  started_at?: string
  finished_at?: string
  tool_name?: string
  tool_input_summary?: string
  tool_output_summary?: string
  evidence_used?: string[]
  error_info?: string
}

/** 总览页数据 */
export interface DashboardSummary {
  total_devices: number
  normal_count: number
  warning_count: number
  fault_count: number
  pending_problems: number
  recent_drafts: MaintenanceDraft[]
  device_status_distribution: { name: string; value: number }[]
  latest_workflow?: WorkflowRun
}

/** 设备创建/更新参数 */
export interface DeviceFormData {
  name: string
  model: string
  area: string
  status: DeviceStatus
  rated_pressure: number
  rated_power: number
  commissioned_at: string
}

/** 问题创建/更新参数 */
export interface ProblemFormData {
  device_id: string
  symptom: string
  severity: ProblemSeverity
  status: ProblemStatus
  description: string
  possible_causes: string[]
  source: string
}

/** API 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 列表查询参数 */
export interface ListQuery {
  page?: number
  page_size?: number
  search?: string
  status?: string
  severity?: string
  device_id?: string
}

/** 设备详情完整数据 */
export interface DeviceDetail extends Device {
  status_history: DeviceStatusRecord[]
  historical_faults: HistoricalFault[]
  related_components: RelatedComponent[]
  related_cases: RelatedCase[]
  related_drafts: RelatedDraft[]
}
