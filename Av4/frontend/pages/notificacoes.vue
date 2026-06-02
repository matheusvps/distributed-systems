<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useNotificacoesStore } from '~/stores/notificacoes'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'
import { useSse } from '~/composables/useSse'
import type { NotificationEvent, SseStatus } from '~/types'

const store = useNotificacoesStore()
const user = useUserStore()
const toast = useToast()

const { status, connect } = useSse({
  onMessage(raw) {
    try {
      const data = JSON.parse(raw) as NotificationEvent
      store.add(data)
    } catch {
      // Some gateways send a plain string; wrap it defensively.
      store.add({ type: 'categoria', message: String(raw) })
    }
  },
  onReady() {
    toast.success('Conectado ao stream de notificações')
  }
})

onMounted(() => connect(user.consumerId))
watch(() => user.consumerId, (id) => connect(id))

const statusMeta = computed<Record<SseStatus, { label: string; dot: string; text: string }>>(() => ({
  idle: { label: 'Inativo', dot: 'bg-slate-300', text: 'text-slate-400' },
  connecting: { label: 'Conectando…', dot: 'bg-amber-400 animate-pulse', text: 'text-amber-600' },
  open: { label: 'Ao vivo', dot: 'bg-emerald-500 animate-pulse', text: 'text-emerald-600' },
  error: { label: 'Reconectando…', dot: 'bg-rose-500 animate-pulse', text: 'text-rose-600' },
  closed: { label: 'Desconectado', dot: 'bg-slate-400', text: 'text-slate-400' }
}))
const meta = computed(() => statusMeta.value[status.value])

const fmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
function price(v?: number) {
  return typeof v === 'number' ? fmt.format(v) : null
}
function time(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR')
}
function icon(type: string) {
  return type === 'hotdeal' ? '🔥' : '🛎️'
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader title="Notificações ao vivo" :subtitle="`Stream em tempo real para ${user.consumerId}`">
      <template #actions>
        <span
          class="badge bg-white ring-1 ring-inset ring-slate-200"
          :class="meta.text"
        >
          <span class="h-2 w-2 rounded-full" :class="meta.dot" />
          {{ meta.label }}
        </span>
        <button
          v-if="store.feed.length"
          class="btn-ghost btn-sm"
          @click="store.clear()"
        >
          Limpar
        </button>
      </template>
    </PageHeader>

    <div class="mb-5 grid grid-cols-3 gap-3">
      <div class="card p-4">
        <p class="text-xs text-slate-400">Total</p>
        <p class="text-xl font-bold text-slate-900">{{ store.unread }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-400">🔥 Hot deals</p>
        <p class="text-xl font-bold text-orange-600">{{ store.hotCount }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-400">🛎️ Categorias</p>
        <p class="text-xl font-bold text-brand-600">{{ store.categoriaCount }}</p>
      </div>
    </div>

    <EmptyState
      v-if="!store.feed.length"
      icon="🛎️"
      title="Aguardando notificações"
      subtitle="Siga categorias em Interesses e mantenha esta página aberta para ver eventos chegando em tempo real."
    />

    <ul v-else class="space-y-3">
      <TransitionGroup name="feed">
        <li
          v-for="n in store.feed"
          :key="n.localId"
          class="card flex gap-3 p-4"
          :class="n.type === 'hotdeal' ? 'border-l-4 border-l-orange-400' : 'border-l-4 border-l-brand-400'"
        >
          <div class="text-2xl leading-none">{{ icon(n.type) }}</div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span
                class="badge"
                :class="n.type === 'hotdeal' ? 'bg-orange-100 text-orange-700' : 'bg-brand-50 text-brand-700'"
              >
                {{ n.type === 'hotdeal' ? 'Hot deal' : 'Categoria' }}
              </span>
              <CategoryBadge :category="n.category" />
              <span v-if="n.tag" class="badge bg-slate-100 text-slate-500">{{ n.tag }}</span>
              <span class="ml-auto text-xs text-slate-400">{{ time(n.receivedAt) }}</span>
            </div>
            <p class="mt-1 text-sm font-medium text-slate-800">
              {{ n.title || n.message }}
            </p>
            <p v-if="n.title && n.message" class="text-sm text-slate-500">{{ n.message }}</p>
            <div class="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-400">
              <span v-if="n.store">🏬 {{ n.store }}</span>
              <span v-if="price(n.price)">{{ price(n.price) }}</span>
              <span v-if="typeof n.score === 'number'">⭐ {{ n.score }}</span>
            </div>
          </div>
        </li>
      </TransitionGroup>
    </ul>
  </div>
</template>

<style scoped>
.feed-enter-active {
  transition: all 0.3s ease;
}
.feed-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
