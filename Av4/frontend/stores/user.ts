import { defineStore } from 'pinia'

export type Role = 'cliente' | 'loja' | null

const KEYS = {
  role: 'promo.role',
  consumerId: 'promo.consumerId',
  loja: 'promo.loja'
}

export const useUserStore = defineStore('user', {
  state: () => ({
    role: null as Role,
    consumerId: 'cliente_a',
    loja: { name: '', email: '' }
  }),
  getters: {
    isCliente: (s) => s.role === 'cliente',
    isLoja: (s) => s.role === 'loja',
    lojaConfigured: (s) => Boolean(s.loja.name && s.loja.email),
    homePath: (s) => (s.role === 'loja' ? '/loja' : '/')
  },
  actions: {
    hydrate() {
      if (typeof window === 'undefined') return
      const role = window.localStorage.getItem(KEYS.role)
      if (role === 'cliente' || role === 'loja') this.role = role
      const cid = window.localStorage.getItem(KEYS.consumerId)
      if (cid) this.consumerId = cid
      const loja = window.localStorage.getItem(KEYS.loja)
      if (loja) {
        try {
          const parsed = JSON.parse(loja)
          if (parsed && typeof parsed === 'object') this.loja = { name: parsed.name || '', email: parsed.email || '' }
        } catch {
        }
      }
    },
    persist() {
      if (typeof window === 'undefined') return
      if (this.role) window.localStorage.setItem(KEYS.role, this.role)
      else window.localStorage.removeItem(KEYS.role)
      window.localStorage.setItem(KEYS.consumerId, this.consumerId)
      window.localStorage.setItem(KEYS.loja, JSON.stringify(this.loja))
    },
    setConsumerId(id: string) {
      this.consumerId = id.trim() || 'cliente_a'
      this.persist()
    },
    setLoja(name: string, email: string) {
      this.loja = { name: name.trim(), email: email.trim() }
      this.persist()
    },
    enterAsCliente(id?: string) {
      if (id != null) this.consumerId = id.trim() || 'cliente_a'
      this.role = 'cliente'
      this.persist()
    },
    enterAsLoja(name: string, email: string) {
      this.loja = { name: name.trim(), email: email.trim() }
      this.role = 'loja'
      this.persist()
    },
    exit() {
      this.role = null
      this.persist()
    }
  }
})
