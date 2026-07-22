/**
 * 通用 API Composable -- 为列表/详情页提供统一的 loading/error/data 管理
 */
import { ref, type Ref } from 'vue'

/** useApi 返回类型 */
export interface UseApiReturn<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  execute: (...args: unknown[]) => Promise<void>
}

/**
 * 通用异步数据加载 Composable
 * @param fetcher - 异步数据获取函数
 * @returns { data, loading, error, execute }
 *
 * @example
 * const { data: devices, loading, error, execute } = useApi(() => fetchDevices())
 * await execute()
 */
export function useApi<T>(
  fetcher: (...args: unknown[]) => Promise<T>
): UseApiReturn<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute(...args: unknown[]) {
    loading.value = true
    error.value = null
    try {
      data.value = await fetcher(...args)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '未知错误'
      console.error('[useApi]', e)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
