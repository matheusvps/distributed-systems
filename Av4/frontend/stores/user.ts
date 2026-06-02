import { defineStore } from 'pinia'

const STORAGE_KEY = 'promo.consumerId'

export const useUserStore = defineStore('user', {
  state: () => ({
    consumerId: 'cliente_a'
  }),
  actions: {
    hydrate() {
      if (typeof window === 'undefined') return
      const saved = window.localStorage.getItem(STORAGE_KEY)
      if (saved) this.consumerId = saved
    },
    setConsumerId(id: string) {
      const value = id.trim() || 'cliente_a'
      this.consumerId = value
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(STORAGE_KEY, value)
      }
    }
  }
})
