import { defineStore } from 'pinia'
import type { FeedNotification, NotificationEvent } from '~/types'

const MAX_FEED = 100

export const useNotificacoesStore = defineStore('notificacoes', {
  state: () => ({
    feed: [] as FeedNotification[]
  }),
  getters: {
    // Only items not yet seen count toward the badge.
    unread: (state) => state.feed.filter((n) => !n.read).length,
    hotCount: (state) => state.feed.filter((n) => n.type === 'hotdeal').length,
    categoriaCount: (state) => state.feed.filter((n) => n.type === 'categoria').length
  },
  actions: {
    add(event: NotificationEvent) {
      const item: FeedNotification = {
        ...event,
        receivedAt: new Date().toISOString(),
        localId: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        read: false
      }
      this.feed.unshift(item)
      if (this.feed.length > MAX_FEED) this.feed.length = MAX_FEED
    },
    /** Marca tudo como lido — chamado ao abrir o painel. */
    markAllRead() {
      this.feed.forEach((n) => {
        n.read = true
      })
    },
    /** Descarta o que já foi lido — chamado ao fechar o painel,
     *  para que notificações antigas não reapareçam ao reabrir. */
    dropRead() {
      this.feed = this.feed.filter((n) => !n.read)
    },
    clear() {
      this.feed = []
    }
  }
})
