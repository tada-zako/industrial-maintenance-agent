/** HTTP 请求封装，基于原生 Fetch。 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

/** 只有显式配置 VITE_USE_MOCK=true 时才使用前端 Mock 数据。 */
export function isMockEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK === 'true'
}

/** 通用 Fetch 包装，自动处理 JSON 和错误 */
export async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`)
  }

  return res.json()
}

/** 带 Mock 回退的请求：先尝试真实 API，失败且开启 Mock 时使用 mock 数据 */
export async function requestWithMock<T>(
  path: string,
  mockData: () => Promise<T>,
  options?: RequestInit
): Promise<T> {
  if (isMockEnabled()) {
    return mockData()
  }

  try {
    return await request<T>(path, options)
  } catch {
    if (import.meta.env.DEV) {
      console.warn(`[API] ${path} 请求失败，回退到 Mock 数据`)
      return mockData()
    }
    throw new Error(`API 请求失败: ${path}`)
  }
}

export function get<T>(path: string) {
  return request<T>(path, { method: 'GET' })
}

export function post<T>(path: string, body?: unknown) {
  return request<T>(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
}

export function patch<T>(path: string, body?: unknown) {
  return request<T>(path, {
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  })
}

export function del<T>(path: string) {
  return request<T>(path, { method: 'DELETE' })
}

/** 模拟网络延迟 */
export function delay(ms = 300): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
