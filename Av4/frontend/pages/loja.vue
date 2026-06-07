<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Promotion } from '~/types'
import { useApiService } from '~/services/api'
import { useUserStore } from '~/stores/user'
import { useMinhasStore } from '~/stores/minhas'

const api = useApiService()
const user = useUserStore()
const minhas = useMinhasStore()

const catalog = ref<Promotion[]>([])
const loading = ref(false)
const error = ref('')

const fmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const sameStore = (a?: string, b?: string) =>
  (a || '').trim().toLowerCase() === (b || '').trim().toLowerCase()

interface Row {
  id: string
  title?: string
  category?: string
  price?: number
  originalPrice?: number
  status: string
  hot: boolean
  score?: number
  pending: boolean
}

const rows = computed<Row[]>(() => {
  const mine = catalog.value.filter((p) => sameStore(p.store, user.loja.name))
  const published: Row[] = mine.map((p) => ({
    id: p.id,
    title: p.title,
    category: p.category,
    price: p.price,
    originalPrice: p.originalPrice,
    status: p.status || 'published',
    hot: Boolean(p.hot),
    score: p.score,
    pending: false
  }))
  const publishedIds = new Set(published.map((r) => r.id))
  const pending: Row[] = minhas.submissions
    .filter((s) => sameStore(s.store, user.loja.name) && !publishedIds.has(s.id))
    .map((s) => ({
      id: s.id,
      title: s.title,
      category: s.category,
      price: s.price,
      originalPrice: s.originalPrice,
      status: 'validando',
      hot: false,
      score: 0,
      pending: true
    }))
  return [...pending, ...published]
})

const stats = computed(() => ({
  total: rows.value.length,
  publicadas: rows.value.filter((r) => !r.pending).length,
  hot: rows.value.filter((r) => r.hot).length
}))

function discount(p: Row) {
  if (typeof p.price === 'number' && typeof p.originalPrice === 'number' && p.originalPrice > 0 && p.price < p.originalPrice) {
    return Math.round((1 - p.price / p.originalPrice) * 100)
  }
  return null
}
function money(v?: number) {
  return typeof v === 'number' ? fmt.format(v) : null
}

function statusMeta(r: Row) {
  if (r.pending) return { label: 'Validando', cls: 'bg-amber-100 text-amber-700', icon: 'clock' }
  if (r.hot) return { label: 'Hot deal', cls: 'bg-acid-300 text-pine-900', icon: 'flame' }
  return { label: 'Publicada', cls: 'bg-pine-50 text-pine-700 ring-1 ring-inset ring-pine-100', icon: 'check' }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getPromotions({})
    catalog.value = res?.promotions ?? []
    minhas.prunePublished(catalog.value.map((p) => p.id))
  } catch (e: any) {
    error.value = e?.data?.message || e?.message || 'Falha ao carregar promoções'
    catalog.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader
      eyebrow="Painel da loja"
      title="Minhas promoções"
      :subtitle="`Ofertas publicadas por ${user.loja.name}, com status e desempenho em tempo real.`"
    >
      <template #actions>
        <button class="btn-ghost btn-sm" :disabled="loading" @click="load">
          <Icon name="refresh" :size="15" :class="loading ? 'animate-spin' : ''" /> Atualizar
        </button>
        <NuxtLink to="/cadastro" class="btn-accent btn-sm">
          <Icon name="plus" :size="15" :stroke-width="2.25" /> Nova promoção
        </NuxtLink>
      </template>
    </PageHeader>

    <!-- Resumo -->
    <div class="mb-6 grid grid-cols-3 gap-3">
      <div class="card p-4">
        <p class="text-xs font-medium uppercase tracking-wider text-ink-400">Total</p>
        <p class="nums mt-1 text-2xl font-bold text-ink-900">{{ stats.total }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs font-medium uppercase tracking-wider text-ink-400">Publicadas</p>
        <p class="nums mt-1 text-2xl font-bold text-pine-600">{{ stats.publicadas }}</p>
      </div>
      <div class="card p-4">
        <p class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-ink-400">
          <Icon name="flame" :size="13" /> Hot deals
        </p>
        <p class="nums mt-1 text-2xl font-bold text-acid-600">{{ stats.hot }}</p>
      </div>
    </div>

    <div v-if="loading && !rows.length" class="space-y-3">
      <div v-for="n in 3" :key="n" class="card animate-pulse p-4">
        <div class="h-4 w-1/3 rounded bg-bone-200" />
        <div class="mt-2 h-3 w-1/4 rounded bg-bone-200" />
      </div>
    </div>

    <EmptyState
      v-else-if="error"
      icon="alert"
      title="Erro ao carregar"
      :subtitle="error"
    >
      <button class="btn-primary btn-sm mt-4" @click="load">Tentar novamente</button>
    </EmptyState>

    <EmptyState
      v-else-if="!rows.length"
      icon="trending"
      title="Nenhuma promoção ainda"
      subtitle="Cadastre sua primeira oferta — ela aparece aqui assim que for enviada."
    >
      <NuxtLink to="/cadastro" class="btn-accent btn-sm mt-4">
        <Icon name="plus" :size="15" :stroke-width="2.25" /> Cadastrar promoção
      </NuxtLink>
    </EmptyState>

    <ul v-else class="space-y-2.5">
      <li
        v-for="r in rows"
        :key="r.id"
        class="card flex flex-wrap items-center gap-x-4 gap-y-2 p-4"
        :class="r.pending ? 'border-dashed' : ''"
      >
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="badge inline-flex items-center gap-1" :class="statusMeta(r).cls">
              <Icon :name="statusMeta(r).icon" :size="12" /> {{ statusMeta(r).label }}
            </span>
            <CategoryBadge :category="r.category" />
          </div>
          <p class="mt-1.5 font-display text-base font-bold text-ink-900">{{ r.title || 'Sem título' }}</p>
        </div>

        <div class="flex items-center gap-5">
          <div class="text-right">
            <div class="flex items-baseline gap-1.5">
              <span v-if="money(r.price)" class="nums text-lg font-bold text-pine-800">{{ money(r.price) }}</span>
              <span v-if="discount(r)" class="nums text-xs font-semibold text-acid-700">-{{ discount(r) }}%</span>
            </div>
            <span v-if="money(r.originalPrice) && discount(r)" class="nums text-xs text-ink-400 line-through">
              {{ money(r.originalPrice) }}
            </span>
          </div>
          <div class="flex w-16 flex-col items-center rounded-xl bg-bone-100 px-2 py-1.5">
            <span class="nums text-base font-bold" :class="r.pending ? 'text-ink-300' : 'text-ink-900'">
              {{ r.pending ? '—' : (r.score ?? 0) }}
            </span>
            <span class="text-[0.6rem] uppercase tracking-wide text-ink-400">score</span>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>
