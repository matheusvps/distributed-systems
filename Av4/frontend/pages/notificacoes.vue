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
  idle: { label: 'Inativo', dot: 'bg-bone-400', text: 'text-ink-400' },
  connecting: { label: 'Conectando…', dot: 'bg-amber-400 animate-pulse', text: 'text-amber-600' },
  open: { label: 'Ao vivo', dot: 'bg-pine-500 animate-pulse', text: 'text-pine-600' },
  error: { label: 'Reconectando…', dot: 'bg-rose-500 animate-pulse', text: 'text-rose-600' },
  closed: { label: 'Desconectado', dot: 'bg-bone-400', text: 'text-ink-400' }
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
  return type === 'hotdeal' ? 'flame' : 'bell'
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader
      eyebrow="Tempo real"
      title="Notificações ao vivo"
      :subtitle="`Stream de eventos em tempo real para ${user.consumerId}.`"
    >
      <template #actions>
        <span
          class="badge bg-bone-50 ring-1 ring-inset ring-bone-300"
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

    <div class="mb-6 grid grid-cols-3 gap-3">
      <div class="card p-4">
        <p class="text-xs font-medium uppercase tracking-wider text-ink-400">Total</p>
        <p class="nums mt-1 text-2xl font-bold text-ink-900">{{ store.unread }}</p>
      </div>
      <div class="card p-4">
        <p class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-ink-400">
          <Icon name="flame" :size="13" /> Hot deals
        </p>
        <p class="nums mt-1 text-2xl font-bold text-acid-600">{{ store.hotCount }}</p>
      </div>
      <div class="card p-4">
        <p class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-ink-400">
          <Icon name="bell" :size="13" /> Categorias
        </p>
        <p class="nums mt-1 text-2xl font-bold text-pine-600">{{ store.categoriaCount }}</p>
      </div>
    </div>

    <EmptyState
      v-if="!store.feed.length"
      icon="bell"
      title="Aguardando notificações"
      subtitle="Siga categorias em Interesses e mantenha esta página aberta para ver eventos chegando em tempo real."
    />

    <ul v-else class="space-y-3">
      <TransitionGroup name="feed">
        <li
          v-for="n in store.feed"
          :key="n.localId"
          class="card flex gap-4 p-4"
          :class="n.type === 'hotdeal' ? 'border-l-4 border-l-acid-400' : 'border-l-4 border-l-pine-500'"
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
            :class="n.type === 'hotdeal' ? 'bg-acid-100 text-acid-700' : 'bg-pine-50 text-pine-700'"
          >
            <Icon :name="icon(n.type)" :size="20" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span
                class="badge"
                :class="n.type === 'hotdeal' ? 'bg-acid-300 text-pine-900' : 'bg-pine-50 text-pine-700 ring-1 ring-inset ring-pine-100'"
              >
                {{ n.type === 'hotdeal' ? 'Hot deal' : 'Categoria' }}
              </span>
              <CategoryBadge :category="n.category" />
              <span v-if="n.tag" class="badge bg-bone-200 text-ink-500">{{ n.tag }}</span>
              <span class="nums ml-auto text-xs text-ink-400">{{ time(n.receivedAt) }}</span>
            </div>
            <p class="mt-1.5 text-sm font-semibold text-ink-900">
              {{ n.title || n.message }}
            </p>
            <p v-if="n.title && n.message" class="text-sm text-ink-500">{{ n.message }}</p>
            <div class="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-400">
              <span v-if="n.store" class="inline-flex items-center gap-1.5">
                <Icon name="store" :size="13" /> {{ n.store }}
              </span>
              <span v-if="price(n.price)" class="nums">{{ price(n.price) }}</span>
              <span v-if="typeof n.score === 'number'" class="inline-flex items-center gap-1.5">
                <Icon name="trending" :size="13" /> <span class="nums">{{ n.score }}</span>
              </span>
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
