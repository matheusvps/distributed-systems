import { defineStore } from 'pinia'
import type { Promotion } from '~/types'

export const usePromocoesStore = defineStore('promocoes', {
  state: () => ({
    items: [] as Promotion[],
    categories: [] as string[],
    selectedCategory: '' as string,
    loading: false,
    error: '' as string,
    count: 0
  }),
  getters: {
    hotDeals: (state) => state.items.filter((p) => p.hot)
  },
  actions: {
    async fetchCategories() {
      try {
        const api = useApiService()
        const res = await api.getCategories()
        this.categories = res?.categories ?? []
      } catch (e: any) {
        this.categories = []
      }
    },

    async fetchPromotions(params: { category?: string; hot?: boolean } = {}) {
      this.loading = true
      this.error = ''
      try {
        const api = useApiService()
        const res = await api.getPromotions(params)
        this.items = res?.promotions ?? []
        this.count = res?.count ?? this.items.length
      } catch (e: any) {
        this.error = e?.data?.message || e?.message || 'Falha ao carregar promoções'
        this.items = []
        this.count = 0
      } finally {
        this.loading = false
      }
    },

    async createPromotion(payload: any) {
      const api = useApiService()
      return await api.createPromotion(payload)
    },

    async vote(promotionId: string, vote: 1 | -1, consumerId: string) {
      const api = useApiService()
      const promo = this.items.find((p) => p.id === promotionId)
      if (promo && typeof promo.score === 'number') {
        promo.score += vote
      }
      await api.vote(promotionId, { vote, consumerId })
    }
  }
})
