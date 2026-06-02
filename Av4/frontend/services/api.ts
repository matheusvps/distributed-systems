import type {
  PromotionsResponse,
  CreatePromotionPayload,
  VotePayload,
  InterestsResponse,
  CategoriesResponse
} from '~/types'

/**
 * Centralized REST calls to the Gateway. Stores consume this service.
 */
export function useApiService() {
  const api = useApi()

  return {
    baseURL: api.baseURL,

    getPromotions(params: { category?: string; hot?: boolean } = {}) {
      const query: Record<string, any> = {}
      if (params.category) query.category = params.category
      if (params.hot != null) query.hot = params.hot
      return api.get<PromotionsResponse>('/api/promocoes', query)
    },

    createPromotion(payload: CreatePromotionPayload) {
      return api.post<{ promotionId: string }>('/api/promocoes', payload)
    },

    vote(promotionId: string, payload: VotePayload) {
      return api.post<unknown>(`/api/promocoes/${encodeURIComponent(promotionId)}/voto`, payload)
    },

    getInterests(consumerId: string) {
      return api.get<InterestsResponse>('/api/interesses', { consumerId })
    },

    addInterest(consumerId: string, category: string) {
      return api.post<unknown>('/api/interesses', { consumerId, category })
    },

    removeInterest(consumerId: string, category: string) {
      return api.del<unknown>('/api/interesses', { consumerId, category })
    },

    getCategories() {
      return api.get<CategoriesResponse>('/api/categorias')
    },

    health() {
      return api.get<unknown>('/api/health')
    }
  }
}
