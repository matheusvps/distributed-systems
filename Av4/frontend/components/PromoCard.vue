<script setup lang="ts">
import { computed } from 'vue'
import type { Promotion } from '~/types'

const props = defineProps<{ promo: Promotion; voting?: boolean }>()
const emit = defineEmits<{ (e: 'vote', vote: 1 | -1): void }>()

const fmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

const price = computed(() =>
  typeof props.promo.price === 'number' ? fmt.format(props.promo.price) : null
)
const original = computed(() =>
  typeof props.promo.originalPrice === 'number' ? fmt.format(props.promo.originalPrice) : null
)
const discount = computed(() => {
  const { price: p, originalPrice: o } = props.promo
  if (typeof p === 'number' && typeof o === 'number' && o > 0 && p < o) {
    return Math.round((1 - p / o) * 100)
  }
  return null
})
</script>

<template>
  <article class="card group flex flex-col p-5 hover:-translate-y-0.5 hover:shadow-cardhover">
    <header class="mb-3 flex items-start justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <CategoryBadge :category="promo.category" />
        <span v-if="promo.hot" class="badge bg-orange-100 text-orange-700">🔥 Hot deal</span>
        <span
          v-if="promo.status && promo.status !== 'published'"
          class="badge bg-slate-100 text-slate-500"
        >
          {{ promo.status }}
        </span>
      </div>
      <span
        v-if="discount"
        class="badge shrink-0 bg-emerald-100 text-emerald-700"
        title="Desconto"
      >
        -{{ discount }}%
      </span>
    </header>

    <h3 class="text-base font-semibold text-slate-900">
      {{ promo.title || 'Sem título' }}
    </h3>
    <p v-if="promo.description" class="mt-1 line-clamp-3 text-sm text-slate-500">
      {{ promo.description }}
    </p>

    <div class="mt-4 flex items-end gap-2">
      <span v-if="price" class="text-2xl font-bold text-slate-900">{{ price }}</span>
      <span v-if="original && discount" class="pb-1 text-sm text-slate-400 line-through">
        {{ original }}
      </span>
    </div>

    <div class="mt-3 flex items-center gap-3 text-xs text-slate-500">
      <span v-if="promo.store" class="inline-flex items-center gap-1">
        🏬 {{ promo.store }}
      </span>
      <span v-if="typeof promo.score === 'number'" class="inline-flex items-center gap-1">
        ⭐ {{ promo.score }}
      </span>
    </div>

    <footer class="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4">
      <button
        class="btn-ghost btn-sm flex-1 hover:border-emerald-300 hover:text-emerald-700"
        :disabled="voting"
        @click="emit('vote', 1)"
      >
        👍 Curtir
      </button>
      <button
        class="btn-ghost btn-sm flex-1 hover:border-rose-300 hover:text-rose-700"
        :disabled="voting"
        @click="emit('vote', -1)"
      >
        👎 Não curtir
      </button>
    </footer>
  </article>
</template>
