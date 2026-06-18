import { defineStore } from 'pinia'

const STORAGE_KEY = 'promo.loja.submissions'

export interface Submission {
  id: string
  title: string
  category: string
  price: number
  originalPrice: number
  store: string
  storeEmail: string
  submittedAt: string
}

export const useMinhasStore = defineStore('minhas', {
  state: () => ({
    submissions: [] as Submission[]
  }),
  actions: {
    hydrate() {
      if (typeof window === 'undefined') return
      const raw = window.localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      try {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) this.submissions = parsed
      } catch {
      }
    },
    persist() {
      if (typeof window === 'undefined') return
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(this.submissions))
    },
    add(sub: Submission) {
      this.submissions.unshift(sub)
      this.persist()
    },
    prunePublished(publishedIds: string[]) {
      const set = new Set(publishedIds)
      const before = this.submissions.length
      this.submissions = this.submissions.filter((s) => !set.has(s.id))
      if (this.submissions.length !== before) this.persist()
    }
  }
})
