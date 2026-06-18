<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useNotificacoesStore } from '~/stores/notificacoes'
import { useUserStore } from '~/stores/user'
import { useSse } from '~/composables/useSse'
import { useNotificationPanel } from '~/composables/useNotificationPanel'
import type { NotificationEvent, SseStatus } from '~/types'

const store = useNotificacoesStore()
const user = useUserStore()
const { open, close } = useNotificationPanel()

const { status, connect } = useSse({
  onMessage(raw) {
    try {
      store.add(JSON.parse(raw) as NotificationEvent)
    } catch {
      store.add({ type: 'categoria', message: String(raw) })
    }
  }
})

onMounted(() => connect(user.consumerId))
watch(() => user.consumerId, (id) => connect(id))

watch(open, (isOpen, wasOpen) => {
  if (isOpen) store.markAllRead()
  else if (wasOpen) store.dropRead()
})
watch(
  () => store.feed.length,
  () => {
    if (open.value) store.markAllRead()
  }
)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

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
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[90] bg-pine-950/40 backdrop-blur-sm"
        @click="close"
      />
    </Transition>

    <Transition name="drawer">
      <aside
        v-if="open"
        class="fixed inset-y-0 right-0 z-[95] flex w-full max-w-md flex-col border-l border-bone-200 bg-bone-100 shadow-cardhover"
        role="dialog"
        aria-label="Notificações"
      >
        <header class="flex items-center gap-3 border-b border-bone-200 px-5 py-4">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-pine-800 text-acid-300">
            <Icon name="bell" :size="20" />
          </div>
          <div class="min-w-0 flex-1">
            <h2 class="font-display text-lg font-bold leading-tight text-ink-900">Notificações</h2>
            <span class="inline-flex items-center gap-1.5 text-xs font-medium" :class="meta.text">
              <span class="h-1.5 w-1.5 rounded-full" :class="meta.dot" />
              {{ meta.label }} · {{ user.consumerId }}
            </span>
          </div>
          <button
            v-if="store.feed.length"
            class="btn-ghost btn-sm"
            @click="store.clear()"
          >
            Limpar
          </button>
          <button
            class="flex h-9 w-9 items-center justify-center rounded-lg text-ink-500 transition hover:bg-bone-200 hover:text-ink-900"
            aria-label="Fechar"
            @click="close"
          >
            <Icon name="close" :size="18" />
          </button>
        </header>

        <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          <div
            v-if="!store.feed.length"
            class="flex h-full flex-col items-center justify-center px-6 text-center"
          >
            <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-bone-200 text-pine-700">
              <Icon name="bell" :size="26" />
            </div>
            <h3 class="font-display text-base font-bold text-ink-900">Tudo em dia</h3>
            <p class="mt-1.5 max-w-xs text-sm text-ink-500">
              Siga categorias em Interesses para receber novas ofertas aqui em tempo real.
            </p>
            <NuxtLink to="/interesses" class="btn-ghost btn-sm mt-5" @click="close">
              <Icon name="bookmark" :size="15" /> Gerenciar interesses
            </NuxtLink>
          </div>

          <ul v-else class="space-y-2.5">
            <TransitionGroup name="feed">
              <li
                v-for="n in store.feed"
                :key="n.localId"
                class="card flex gap-3 p-3.5"
                :class="n.type === 'hotdeal' ? 'border-l-4 border-l-acid-400' : 'border-l-4 border-l-pine-500'"
              >
                <div
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                  :class="n.type === 'hotdeal' ? 'bg-acid-100 text-acid-700' : 'bg-pine-50 text-pine-700'"
                >
                  <Icon :name="icon(n.type)" :size="18" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span
                      class="badge"
                      :class="n.type === 'hotdeal' ? 'bg-acid-300 text-pine-900' : 'bg-pine-50 text-pine-700 ring-1 ring-inset ring-pine-100'"
                    >
                      {{ n.type === 'hotdeal' ? 'Hot deal' : 'Categoria' }}
                    </span>
                    <CategoryBadge :category="n.category" />
                    <span class="nums ml-auto text-xs text-ink-400">{{ time(n.receivedAt) }}</span>
                  </div>
                  <p class="mt-1 text-sm font-semibold text-ink-900">{{ n.title || n.message }}</p>
                  <p v-if="n.title && n.message" class="text-sm text-ink-500">{{ n.message }}</p>
                  <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-400">
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
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.32s cubic-bezier(0.2, 0.7, 0.2, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
}
.feed-enter-active {
  transition: all 0.3s ease;
}
.feed-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
