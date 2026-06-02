/**
 * Typed fetch wrapper around the Gateway base URL from runtimeConfig.
 * All REST traffic goes through here.
 */
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.gatewayUrl as string

  async function request<T>(path: string, options: any = {}): Promise<T> {
    return await $fetch<T>(path, {
      baseURL,
      ...options
    })
  }

  return {
    baseURL,
    get: <T>(path: string, query?: Record<string, any>) =>
      request<T>(path, { method: 'GET', query }),
    post: <T>(path: string, body?: any) =>
      request<T>(path, { method: 'POST', body }),
    del: <T>(path: string, body?: any) =>
      request<T>(path, { method: 'DELETE', body })
  }
}
