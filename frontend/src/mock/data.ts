/**
 * Mock 数据层 -- 模拟后端 API 返回数据
 * 当 VITE_USE_MOCK=true 时生效，后端就绪后可移除
 */
import type {
  Device,
  DashboardSummary,
  Problem,
  MaintenanceDraft,
  WorkflowRun,
  DeviceDetail,
  RunningIndicators,
  DeviceStatusRecord,
  HistoricalFault,
  RelatedComponent,
  RelatedCase,
  RelatedDraft,
} from '../types'

// ===================== 设备数据 =====================

export const mockDevices: Device[] = [
  {
    id: 'dev-001', name: '空压机 A-1', model: 'SA-75A 螺杆空压机',
    area: 'A区-冲压车间', status: 'normal', updated_at: '2026-07-22T08:30:00Z',
    rated_pressure: 0.8, rated_power: 75, commissioned_at: '2023-03-15',
    running_indicators: {
      id: 'ri-001a', device_id: 'dev-001', running_status: '运行中',
      exhaust_pressure: 0.75, temperature: 72, vibration: 2.1, oil_level: '正常',
      collected_at: '2026-07-22T08:25:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-002', name: '空压机 A-2', model: 'CA-55B 离心空压机',
    area: 'A区-冲压车间', status: 'warning', updated_at: '2026-07-22T07:15:00Z',
    rated_pressure: 1.0, rated_power: 55, commissioned_at: '2024-01-10',
    running_indicators: {
      id: 'ri-002a', device_id: 'dev-002', running_status: '运行中',
      exhaust_pressure: 0.92, temperature: 88, vibration: 4.8, oil_level: '偏低',
      collected_at: '2026-07-22T07:10:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-003', name: '空压机 B-1', model: 'SA-75A 螺杆空压机',
    area: 'B区-焊接车间', status: 'normal', updated_at: '2026-07-22T08:00:00Z',
    rated_pressure: 0.8, rated_power: 75, commissioned_at: '2023-06-20',
    running_indicators: {
      id: 'ri-003a', device_id: 'dev-003', running_status: '运行中',
      exhaust_pressure: 0.78, temperature: 68, vibration: 1.8, oil_level: '正常',
      collected_at: '2026-07-22T07:55:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-004', name: '空压机 B-2', model: 'PA-30C 活塞空压机',
    area: 'B区-焊接车间', status: 'normal', updated_at: '2026-07-21T23:00:00Z',
    rated_pressure: 0.7, rated_power: 30, commissioned_at: '2022-11-05',
    running_indicators: {
      id: 'ri-004a', device_id: 'dev-004', running_status: '待机',
      exhaust_pressure: 0.05, temperature: 35, vibration: 0.5, oil_level: '正常',
      collected_at: '2026-07-21T22:55:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-005', name: '空压机 C-1', model: 'SA-75A 螺杆空压机',
    area: 'C区-涂装车间', status: 'normal', updated_at: '2026-07-22T08:10:00Z',
    rated_pressure: 0.8, rated_power: 75, commissioned_at: '2023-09-12',
    running_indicators: {
      id: 'ri-005a', device_id: 'dev-005', running_status: '运行中',
      exhaust_pressure: 0.76, temperature: 70, vibration: 2.0, oil_level: '正常',
      collected_at: '2026-07-22T08:05:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-006', name: '空压机 C-2', model: 'CA-55B 离心空压机',
    area: 'C区-涂装车间', status: 'fault', updated_at: '2026-07-22T06:45:00Z',
    rated_pressure: 1.0, rated_power: 55, commissioned_at: '2024-02-28',
    running_indicators: {
      id: 'ri-006a', device_id: 'dev-006', running_status: '故障停机',
      exhaust_pressure: 0.32, temperature: 105, vibration: 9.2, oil_level: '过低',
      collected_at: '2026-07-22T06:40:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-007', name: '空压机 D-1', model: 'SA-75A 螺杆空压机',
    area: 'D区-总装车间', status: 'warning', updated_at: '2026-07-22T07:30:00Z',
    rated_pressure: 0.8, rated_power: 75, commissioned_at: '2023-04-18',
    running_indicators: {
      id: 'ri-007a', device_id: 'dev-007', running_status: '运行中',
      exhaust_pressure: 0.70, temperature: 82, vibration: 5.5, oil_level: '正常',
      collected_at: '2026-07-22T07:25:00Z', source: 'PLC采集',
    },
  },
  {
    id: 'dev-008', name: '空压机 D-2', model: 'PA-30C 活塞空压机',
    area: 'D区-总装车间', status: 'normal', updated_at: '2026-07-22T08:20:00Z',
    rated_pressure: 0.7, rated_power: 30, commissioned_at: '2022-12-01',
    running_indicators: {
      id: 'ri-008a', device_id: 'dev-008', running_status: '运行中',
      exhaust_pressure: 0.68, temperature: 65, vibration: 1.5, oil_level: '正常',
      collected_at: '2026-07-22T08:15:00Z', source: 'PLC采集',
    },
  },
]

// ===================== 设备详情（含历史数据） =====================

const mockStatusHistory: Record<string, DeviceStatusRecord[]> = {
  'dev-001': [
    { id: 'sh-001-1', device_id: 'dev-001', running_status: '运行中', exhaust_pressure: 0.76, temperature: 71, vibration: 2.0, oil_level: '正常', collected_at: '2026-07-22T06:00:00Z', source: 'PLC采集' },
    { id: 'sh-001-2', device_id: 'dev-001', running_status: '运行中', exhaust_pressure: 0.74, temperature: 73, vibration: 2.2, oil_level: '正常', collected_at: '2026-07-22T04:00:00Z', source: 'PLC采集' },
    { id: 'sh-001-3', device_id: 'dev-001', running_status: '运行中', exhaust_pressure: 0.77, temperature: 70, vibration: 1.9, oil_level: '正常', collected_at: '2026-07-22T02:00:00Z', source: 'PLC采集' },
    { id: 'sh-001-4', device_id: 'dev-001', running_status: '运行中', exhaust_pressure: 0.75, temperature: 72, vibration: 2.1, oil_level: '正常', collected_at: '2026-07-22T00:00:00Z', source: 'PLC采集' },
    { id: 'sh-001-5', device_id: 'dev-001', running_status: '运行中', exhaust_pressure: 0.78, temperature: 69, vibration: 1.8, oil_level: '正常', collected_at: '2026-07-21T22:00:00Z', source: 'PLC采集' },
  ],
  'dev-006': [
    { id: 'sh-006-1', device_id: 'dev-006', running_status: '故障停机', exhaust_pressure: 0.32, temperature: 105, vibration: 9.2, oil_level: '过低', collected_at: '2026-07-22T06:00:00Z', source: 'PLC采集' },
    { id: 'sh-006-2', device_id: 'dev-006', running_status: '运行中', exhaust_pressure: 0.88, temperature: 92, vibration: 5.8, oil_level: '偏低', collected_at: '2026-07-22T04:00:00Z', source: 'PLC采集' },
    { id: 'sh-006-3', device_id: 'dev-006', running_status: '运行中', exhaust_pressure: 0.90, temperature: 90, vibration: 5.2, oil_level: '正常', collected_at: '2026-07-22T02:00:00Z', source: 'PLC采集' },
    { id: 'sh-006-4', device_id: 'dev-006', running_status: '运行中', exhaust_pressure: 0.91, temperature: 88, vibration: 4.5, oil_level: '正常', collected_at: '2026-07-22T00:00:00Z', source: 'PLC采集' },
    { id: 'sh-006-5', device_id: 'dev-006', running_status: '运行中', exhaust_pressure: 0.93, temperature: 85, vibration: 3.8, oil_level: '正常', collected_at: '2026-07-21T22:00:00Z', source: 'PLC采集' },
  ],
}

const mockHistoricalFaults: Record<string, HistoricalFault[]> = {
  'dev-001': [
    { id: 'hf-001-1', symptom: '排气压力波动', severity: 'low', discovered_at: '2026-06-15', status: 'resolved', description: '进气过滤器部分堵塞，清洁后恢复正常。' },
  ],
  'dev-006': [
    { id: 'hf-006-1', symptom: '排气压力持续下降', severity: 'critical', discovered_at: '2026-07-22T06:30:00Z', status: 'repairing', description: '排气压力从 0.93MPa 骤降至 0.32MPa，温度升至 105°C，振动 9.2mm/s，油位过低，设备自动停机。初步判断为油气分离器堵塞并伴随润滑油泄漏。' },
    { id: 'hf-006-2', symptom: '温度偏高', severity: 'medium', discovered_at: '2026-07-10', status: 'resolved', description: '冷却器结垢，清洗后温度恢复正常。' },
    { id: 'hf-006-3', symptom: '振动偏大', severity: 'medium', discovered_at: '2026-05-20', status: 'resolved', description: '联轴器对中偏差，重新校准后恢复正常。' },
  ],
}

const mockComponents: Record<string, RelatedComponent[]> = {
  'dev-001': [
    { id: 'c-001-1', name: '螺杆主机', type: '核心部件' },
    { id: 'c-001-2', name: '进气过滤器', type: '过滤系统' },
    { id: 'c-001-3', name: '油气分离器', type: '分离系统' },
    { id: 'c-001-4', name: '冷却器', type: '冷却系统' },
    { id: 'c-001-5', name: '电动机', type: '驱动系统' },
  ],
  'dev-006': [
    { id: 'c-006-1', name: '离心叶轮', type: '核心部件' },
    { id: 'c-006-2', name: '进气导叶', type: '进气系统' },
    { id: 'c-006-3', name: '油气分离器', type: '分离系统' },
    { id: 'c-006-4', name: '冷却器', type: '冷却系统' },
    { id: 'c-006-5', name: '齿轮增速箱', type: '传动系统' },
    { id: 'c-006-6', name: '润滑油泵', type: '润滑系统' },
  ],
}

const mockCases: Record<string, RelatedCase[]> = {
  'dev-001': [
    { id: 'case-001', title: 'SA-75A 进气过滤器堵塞处理', symptom: '排气压力波动', resolution: '定期清洁或更换进气过滤器，建议每500小时检查。' },
  ],
  'dev-006': [
    { id: 'case-002', title: 'CA-55B 油气分离器堵塞更换', symptom: '排气压力下降、温度升高', resolution: '更换油气分离器滤芯并补充润滑油，检查润滑油管路是否有泄漏。' },
    { id: 'case-003', title: 'CA-55B 冷却器清洗维护', symptom: '运行温度偏高', resolution: '每季度清洗冷却器翅片，检查冷却水流速。' },
  ],
}

const mockDeviceDrafts: Record<string, RelatedDraft[]> = {
  'dev-001': [],
  'dev-006': [
    { id: 'draft-001', fault_diagnosis: '油气分离器严重堵塞，导致排气压力骤降并伴随高温', status: 'pending_review', generated_at: '2026-07-22T06:50:00Z' },
  ],
}

// 默认部件（不在上表中时回退）
const defaultComponents: RelatedComponent[] = [
  { id: 'c-def-1', name: '进气系统', type: '进气系统' },
  { id: 'c-def-2', name: '油气分离器', type: '分离系统' },
  { id: 'c-def-3', name: '冷却器', type: '冷却系统' },
  { id: 'c-def-4', name: '电动机', type: '驱动系统' },
]

export function getMockDeviceDetail(deviceId: string): DeviceDetail {
  const device = mockDevices.find((d) => d.id === deviceId)!
  return {
    ...device,
    status_history: mockStatusHistory[deviceId] || [],
    historical_faults: mockHistoricalFaults[deviceId] || [],
    related_components: mockComponents[deviceId] || defaultComponents,
    related_cases: mockCases[deviceId] || [],
    related_drafts: mockDeviceDrafts[deviceId] || [],
  }
}

// ===================== 问题数据 =====================

export const mockProblems: Problem[] = [
  {
    id: 'prob-001', device_id: 'dev-006', device_name: '空压机 C-2',
    symptom: '排气压力持续下降', severity: 'critical', status: 'repairing',
    discovered_at: '2026-07-22T06:30:00Z',
    description: 'CA-55B 离心空压机排气压力从 0.93MPa 骤降至 0.32MPa，温度升至 105°C，振动 9.2mm/s，油位过低，触发自动停机保护。',
    possible_causes: ['油气分离器滤芯严重堵塞', '润滑油管路泄漏', '进气导叶卡滞'],
    source: 'PLC报警', draft_id: 'draft-001',
  },
  {
    id: 'prob-002', device_id: 'dev-002', device_name: '空压机 A-2',
    symptom: '运行温度偏高', severity: 'medium', status: 'investigating',
    discovered_at: '2026-07-21T14:00:00Z',
    description: 'CA-55B 离心空压机持续运行温度偏高（88°C），振动 4.8mm/s，油位偏低，需要排查冷却系统和润滑系统。',
    possible_causes: ['冷却器翅片积灰', '冷却水流量不足', '润滑油老化'],
    source: '巡检发现',
  },
  {
    id: 'prob-003', device_id: 'dev-007', device_name: '空压机 D-1',
    symptom: '振动异常增大', severity: 'medium', status: 'pending',
    discovered_at: '2026-07-22T07:30:00Z',
    description: 'SA-75A 螺杆空压机振动值从正常 2.0mm/s 升至 5.5mm/s，温度正常（82°C），排气压力 0.70MPa 略偏低。',
    possible_causes: ['螺杆转子磨损', '轴承损坏', '联轴器松动'],
    source: 'PLC预警',
  },
  {
    id: 'prob-004', device_id: 'dev-001', device_name: '空压机 A-1',
    symptom: '油位偏低预警', severity: 'low', status: 'pending',
    discovered_at: '2026-07-20T09:00:00Z',
    description: '定期巡检发现油位略有下降，压力温度正常，无明显泄漏痕迹。',
    possible_causes: ['自然消耗', '油气分离器回油管堵塞', '微量泄漏'],
    source: '巡检发现',
  },
  {
    id: 'prob-005', device_id: 'dev-006', device_name: '空压机 C-2',
    symptom: '振动偏大', severity: 'medium', status: 'resolved',
    discovered_at: '2026-05-20T10:00:00Z',
    description: '联轴器对中偏差导致振动偏大，重新校准后恢复正常。',
    possible_causes: ['联轴器对中偏差', '地脚螺栓松动'],
    source: 'PLC预警',
  },
  {
    id: 'prob-006', device_id: 'dev-006', device_name: '空压机 C-2',
    symptom: '温度偏高', severity: 'medium', status: 'resolved',
    discovered_at: '2026-07-10T08:00:00Z',
    description: '冷却器结垢导致冷却效率下降，清洗后恢复正常。',
    possible_causes: ['冷却器结垢', '冷却水水质差'],
    source: 'PLC预警',
  },
]

// ===================== 维修草案数据 =====================

export const mockDrafts: MaintenanceDraft[] = [
  {
    id: 'draft-001', device_id: 'dev-006', device_name: '空压机 C-2', problem_id: 'prob-001',
    fault_diagnosis: '油气分离器严重堵塞并伴随润滑油管路泄漏，导致排气压力骤降、温度异常升高并触发自动停机保护',
    possible_causes: [
      '油气分离器滤芯超周期未更换，压差过大导致滤芯破损',
      '润滑油管路接头松动，密封失效导致微漏',
      '润滑油泵磨损，供油压力不足',
    ],
    check_steps: [
      '断开电源并执行上锁挂牌（LOTO）',
      '检查油气分离器压差表读数，确认是否超限',
      '打开分离器检修口，检查滤芯外观是否有破损或严重堵塞',
      '检查润滑油管路各接头是否有油渍渗漏',
      '使用内窥镜检查齿轮增速箱润滑情况',
      '检查润滑油泵出口压力是否符合要求',
    ],
    repair_steps: [
      '更换油气分离器滤芯（型号 OF-55B-01）',
      '紧固所有润滑油管路接头，更换破损密封垫圈',
      '补充润滑油至标准油位（壳牌 Corena S4 R 46）',
      '检查并清洗冷却器翅片',
      '安装完毕后进行空载试运行 30 分钟，监测各参数',
      '确认压力、温度、振动恢复至正常范围后恢复生产',
    ],
    tools_and_parts: [
      '油气分离器滤芯 OF-55B-01 ×1',
      '润滑油壳牌 Corena S4 R 46 约 20L',
      '密封垫圈套件 SK-55B ×1',
      '扭矩扳手 10-50N·m',
      '内窥镜检查仪',
      '油品分析取样瓶 ×2',
    ],
    safety_notices: [
      '作业前必须执行 LOTO 程序，悬挂"禁止合闸"警示牌',
      '设备停机后需冷却 30 分钟以上方可作业，防止烫伤',
      '润滑油属于危险废物，更换后须按环保要求处置',
      '登高作业（超过 1.5m）须佩戴安全带',
      '试运行时人员须与旋转部件保持安全距离',
    ],
    evidence_refs: [
      { type: 'case', id: 'case-002', label: 'CA-55B 油气分离器堵塞更换案例', relationship: 'APPLIES_TO' },
      { type: 'sop', id: 'sop-001', label: '油气分离器更换标准操作流程', relationship: 'REFER_TO' },
      { type: 'safety', id: 'safe-001', label: '高压设备检修安全规范', relationship: 'REQUIRES' },
      { type: 'material', id: 'mat-001', label: 'CA-55B 维护手册 V3.2', relationship: 'ABOUT_DEVICE' },
    ],
    generated_at: '2026-07-22T06:50:00Z', status: 'pending_review',
    needs_confirmation: true, risk_level: 'high',
  },
  {
    id: 'draft-002', device_id: 'dev-002', device_name: '空压机 A-2',
    fault_diagnosis: '冷却器翅片积灰严重，润滑油老化导致散热效率下降，运行温度持续偏高',
    possible_causes: ['冷却器长期未清洗，翅片积灰', '润滑油超过更换周期', '冷却水流量偏低'],
    check_steps: [
      '检查冷却器进出口温差',
      '目视检查冷却器翅片脏污程度',
      '取样检测润滑油品质',
      '检查冷却水阀门开度和管路',
    ],
    repair_steps: [
      '使用压缩空气和专用清洗剂清洗冷却器翅片',
      '更换润滑油和油过滤器',
      '检查并调整冷却水流量',
    ],
    tools_and_parts: [
      '冷却器清洗剂 CL-500 ×2',
      '润滑油壳牌 Corena S4 R 46 约 25L',
      '油过滤器 OF-55B ×1',
      '压缩空气喷枪',
    ],
    safety_notices: [
      '清洗作业时佩戴护目镜和防尘口罩',
      '作业前断开设备电源',
      '高温部件需冷却后接触',
    ],
    evidence_refs: [
      { type: 'case', id: 'case-003', label: 'CA-55B 冷却器清洗维护案例', relationship: 'APPLIES_TO' },
      { type: 'sop', id: 'sop-002', label: '空压机冷却系统维护SOP', relationship: 'REFER_TO' },
    ],
    generated_at: '2026-07-21T15:00:00Z', status: 'pending_review',
    needs_confirmation: true, risk_level: 'medium',
  },
  {
    id: 'draft-003', device_id: 'dev-007', device_name: '空压机 D-1',
    fault_diagnosis: '螺杆转子轴承磨损初期，导致振动值逐渐增大，暂不影响运行但需安排检修',
    possible_causes: ['轴承磨损', '转子动平衡破坏', '联轴器弹性体老化'],
    check_steps: [
      '频谱分析振动数据，确认频率特征',
      '检查轴承温度和声音',
      '联轴器对中检测',
    ],
    repair_steps: [
      '更换磨损轴承（型号 SKF-6312/C3）',
      '检查并修复转子动平衡',
      '更换联轴器弹性体',
    ],
    tools_and_parts: [
      'SKF-6312/C3 轴承 ×2',
      '联轴器弹性体 R-75A ×1',
      '激光对中仪',
      '振动分析仪',
    ],
    safety_notices: [
      'LOTO 程序必须执行',
      '起吊转子时使用专用吊具',
      '作业区域设置警戒线',
    ],
    evidence_refs: [
      { type: 'sop', id: 'sop-003', label: '螺杆空压机轴承更换SOP', relationship: 'REFER_TO' },
    ],
    generated_at: '2026-07-22T08:00:00Z', status: 'pending_review',
    needs_confirmation: true, risk_level: 'medium',
  },
  {
    id: 'draft-004', device_id: 'dev-001', device_name: '空压机 A-1',
    fault_diagnosis: '油气分离器回油管部分堵塞，导致少量润滑油随压缩空气排出,油位缓慢下降',
    possible_causes: ['回油管积碳堵塞', '回油单向阀卡滞'],
    check_steps: [
      '检查油气分离器排油口流量',
      '拆检回油管路和单向阀',
    ],
    repair_steps: [
      '清洗回油管路',
      '更换回油单向阀',
      '检查并清理回油过滤器',
    ],
    tools_and_parts: [
      '回油单向阀 CV-75A ×1',
      '管路清洗剂 ×1',
    ],
    safety_notices: [
      '设备停机后冷却至 40°C 以下方可作业',
      '拆卸管路时可能有余压残留，缓慢松开接头',
    ],
    evidence_refs: [
      { type: 'sop', id: 'sop-004', label: '油气分离系统维护SOP', relationship: 'REFER_TO' },
    ],
    generated_at: '2026-07-21T10:00:00Z', status: 'confirmed',
    needs_confirmation: false, risk_level: 'low',
  },
  {
    id: 'draft-005', device_id: 'dev-006', device_name: '空压机 C-2',
    fault_diagnosis: '联轴器对中偏差约 0.15mm，已超出允许公差 0.10mm，需要重新校准',
    possible_causes: ['基础沉降', '地脚螺栓松动', '温度变化导致的热膨胀差异'],
    check_steps: [
      '检查地脚螺栓紧固力矩',
      '激光对中仪测量偏差',
      '检查基础沉降情况',
    ],
    repair_steps: [
      '松开机座连接螺栓',
      '激光对中仪重新校准',
      '按扭矩规范重新紧固地脚螺栓',
    ],
    tools_and_parts: [
      '激光对中仪 TKSA-51',
      '扭矩扳手',
      '调整垫片套件',
    ],
    safety_notices: ['LOTO 程序', '校准完成后需进行振动复测'],
    evidence_refs: [
      { type: 'sop', id: 'sop-005', label: '联轴器对中校准SOP', relationship: 'REFER_TO' },
    ],
    generated_at: '2026-05-20T11:00:00Z', status: 'confirmed',
    needs_confirmation: false, risk_level: 'low',
  },
]

// ===================== 工作流数据 =====================

export const mockWorkflows: WorkflowRun[] = [
  {
    id: 'wf-001',
    user_question: '空压机 C-2 排气压力骤降、温度飙升、振动异常，设备已自动停机，请帮我分析故障原因并给出维修方案。',
    device_id: 'dev-006', device_name: '空压机 C-2',
    started_at: '2026-07-22T06:35:00Z',
    finished_at: '2026-07-22T06:50:00Z',
    status: 'completed', draft_id: 'draft-001',
    steps: [
      {
        id: 'ws-001-1', run_id: 'wf-001', step_name: '设备识别与状态查询',
        step_status: 'completed', started_at: '2026-07-22T06:35:00Z', finished_at: '2026-07-22T06:35:15Z',
        tool_name: 'list_devices / get_device_status',
        tool_input_summary: '查询设备 "空压机 C-2" 的当前运行状态',
        tool_output_summary: '设备 ID dev-006，状态故障，排气压力 0.32MPa（正常 0.9-1.0），温度 105°C（正常 <85），振动 9.2mm/s（正常 <4.5），油位过低',
        evidence_used: ['PLC采集数据 2026-07-22T06:40'],
      },
      {
        id: 'ws-001-2', run_id: 'wf-001', step_name: '历史故障查询',
        step_status: 'completed', started_at: '2026-07-22T06:35:20Z', finished_at: '2026-07-22T06:36:00Z',
        tool_name: 'search_problems',
        tool_input_summary: '查询设备 dev-006 的历史故障记录',
        tool_output_summary: '发现 3 条历史记录：温度偏高(7/10)、振动偏大(5/20)、当前排气压力骤降',
        evidence_used: ['故障记录 prob-006（冷却器结垢）', '故障记录 prob-005（振动偏大）'],
      },
      {
        id: 'ws-001-3', run_id: 'wf-001', step_name: '知识图谱查询',
        step_status: 'completed', started_at: '2026-07-22T06:36:05Z', finished_at: '2026-07-22T06:38:00Z',
        tool_name: 'search_knowledge',
        tool_input_summary: '根据故障现象"排气压力骤降+高温+振动异常"查询知识图谱',
        tool_output_summary: '匹配到故障原因：油气分离器堵塞(置信度0.92)、润滑油泄漏(置信度0.85)、进气导叶卡滞(置信度0.45)。匹配到维修措施 3 项、案例 2 项。',
        evidence_used: ['知识图谱节点: FaultCause-油气分离器堵塞', '知识图谱关系: MAY_BE_CAUSED_BY'],
      },
      {
        id: 'ws-001-4', run_id: 'wf-001', step_name: '维修资料检索',
        step_status: 'completed', started_at: '2026-07-22T06:38:05Z', finished_at: '2026-07-22T06:40:00Z',
        tool_name: 'get_maintenance_material',
        tool_input_summary: '检索 CA-55B 型号的 SOP、安全规范和外部资料',
        tool_output_summary: '获取到：油气分离器更换 SOP、高压设备检修安全规范、CA-55B 维护手册 V3.2',
        evidence_used: ['SOP: 油气分离器更换标准操作流程', '安全规范: 高压设备检修安全规范', '外部资料: CA-55B 维护手册 V3.2'],
      },
      {
        id: 'ws-001-5', run_id: 'wf-001', step_name: '生成维修方案草案',
        step_status: 'completed', started_at: '2026-07-22T06:40:10Z', finished_at: '2026-07-22T06:45:00Z',
        tool_name: 'create_repair_draft',
        tool_input_summary: '基于上述查询结果生成结构化维修方案草案',
        tool_output_summary: '生成草案 draft-001，包含故障判断、3 个可能原因、6 个检查步骤、6 个维修步骤、6 项工具备件、5 项安全注意事项',
        evidence_used: ['案例 case-002', 'SOP sop-001', '安全规范 safe-001', '手册 mat-001'],
      },
      {
        id: 'ws-001-6', run_id: 'wf-001', step_name: '草案完整性校验',
        step_status: 'completed', started_at: '2026-07-22T06:45:05Z', finished_at: '2026-07-22T06:46:00Z',
        tool_name: 'validate_repair_draft',
        tool_input_summary: '校验草案 draft-001 的完整性和合规性',
        tool_output_summary: '校验通过：步骤完整、安全注意事项齐全、证据引用有效、工具备件清单完整',
        evidence_used: [],
      },
      {
        id: 'ws-001-7', run_id: 'wf-001', step_name: '保存工作流记录',
        step_status: 'completed', started_at: '2026-07-22T06:46:05Z', finished_at: '2026-07-22T06:50:00Z',
        tool_name: 'record_workflow_run',
        tool_input_summary: '持久化工作流 wf-001 和草案 draft-001',
        tool_output_summary: '保存成功，草案状态设为 pending_review，需人工确认',
        evidence_used: [],
      },
    ],
  },
  {
    id: 'wf-002',
    user_question: '空压机 A-2 最近温度一直偏高，振动也有点大，帮我看看是什么问题？',
    device_id: 'dev-002', device_name: '空压机 A-2',
    started_at: '2026-07-21T14:15:00Z',
    finished_at: '2026-07-21T15:00:00Z',
    status: 'completed', draft_id: 'draft-002',
    steps: [
      {
        id: 'ws-002-1', run_id: 'wf-002', step_name: '设备识别与状态查询',
        step_status: 'completed', started_at: '2026-07-21T14:15:00Z', finished_at: '2026-07-21T14:15:20Z',
        tool_name: 'list_devices / get_device_status',
        tool_input_summary: '查询设备 "空压机 A-2" 状态',
        tool_output_summary: '设备 ID dev-002，状态预警，温度 88°C，振动 4.8mm/s，油位偏低',
      },
      {
        id: 'ws-002-2', run_id: 'wf-002', step_name: '历史故障查询',
        step_status: 'completed', started_at: '2026-07-21T14:15:30Z', finished_at: '2026-07-21T14:18:00Z',
        tool_name: 'search_problems',
        tool_input_summary: '查询设备 dev-002 的历史故障',
        tool_output_summary: '无严重历史故障记录，本次为首次温度偏高报警',
      },
      {
        id: 'ws-002-3', run_id: 'wf-002', step_name: '知识图谱查询',
        step_status: 'completed', started_at: '2026-07-21T14:18:10Z', finished_at: '2026-07-21T14:28:00Z',
        tool_name: 'search_knowledge',
        tool_input_summary: '按"离心空压机+温度偏高+振动偏大"查询知识图谱',
        tool_output_summary: '匹配到：冷却器积灰(0.88)、润滑油老化(0.82)、冷却水不足(0.55)',
      },
      {
        id: 'ws-002-4', run_id: 'wf-002', step_name: '维修资料检索',
        step_status: 'completed', started_at: '2026-07-21T14:28:10Z', finished_at: '2026-07-21T14:35:00Z',
        tool_name: 'get_maintenance_material',
        tool_input_summary: '检索 CA-55B 维护资料',
        tool_output_summary: '获取到冷却器清洗案例和维护 SOP',
      },
      {
        id: 'ws-002-5', run_id: 'wf-002', step_name: '生成维修方案草案',
        step_status: 'completed', started_at: '2026-07-21T14:35:10Z', finished_at: '2026-07-21T14:50:00Z',
        tool_name: 'create_repair_draft',
        tool_input_summary: '生成维护方案草案',
        tool_output_summary: '生成草案 draft-002，建议清洗冷却器并更换润滑油',
      },
      {
        id: 'ws-002-6', run_id: 'wf-002', step_name: '草案完整性校验',
        step_status: 'completed', started_at: '2026-07-21T14:50:10Z', finished_at: '2026-07-21T14:53:00Z',
        tool_name: 'validate_repair_draft',
        tool_input_summary: '校验草案 draft-002',
        tool_output_summary: '校验通过',
      },
      {
        id: 'ws-002-7', run_id: 'wf-002', step_name: '保存工作流记录',
        step_status: 'completed', started_at: '2026-07-21T14:53:10Z', finished_at: '2026-07-21T15:00:00Z',
        tool_name: 'record_workflow_run',
        tool_input_summary: '保存工作流记录',
        tool_output_summary: '保存成功',
      },
    ],
  },
]

// ===================== 总览数据 =====================

export const mockDashboardSummary: DashboardSummary = {
  total_devices: 8,
  normal_count: 5,
  warning_count: 2,
  fault_count: 1,
  pending_problems: 3,
  recent_drafts: mockDrafts.slice(0, 3),
  device_status_distribution: [
    { name: '正常', value: 5 },
    { name: '预警', value: 2 },
    { name: '故障', value: 1 },
  ],
  latest_workflow: mockWorkflows[0],
}

// ===================== 生成 ID 工具 =====================

let _idCounter = 100
export function nextId(prefix: string): string {
  return `${prefix}-${++_idCounter}`
}
