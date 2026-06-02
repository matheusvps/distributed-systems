import { defineStore } from 'pinia'

export const useInteressesStore = defineStore('interesses', {
  state: () => ({
    interests: [] as string[],
    loading: false,
    error: '' as string
  }),
  getters: {
    isFollowing: (state) => (category: string) => state.interests.includes(category)
  },
  actions: {
    async fetch(consumerId: string) {
      this.loading = true
      this.error = ''
      try {
        const api = useApiService()
        const res = await api.getInterests(consumerId)
        this.interests = res?.interests ?? []
      } catch (e: any) {
        this.error = e?.data?.message || e?.message || 'Falha ao carregar interesses'
        this.interests = []
      } finally {
        this.loading = false
      }
    },

    async follow(consumerId: string, category: string) {
      const api = useApiService()
      if (!this.interests.includes(category)) this.interests.push(category)
      try {
        await api.addInterest(consumerId, category)
      } catch (e) {
        this.interests = this.interests.filter((c) => c !== category)
        throw e
      }
    },

    async unfollow(consumerId: string, category: string) {
      const api = useApiService()
      const prev = [...this.interests]
      this.interests = this.interests.filter((c) => c !== category)
      try {
        await api.removeInterest(consumerId, category)
      } catch (e) {
        this.interests = prev
        throw e
      }
    }
  }
})
