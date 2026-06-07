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
  <article
    class="card group relative flex flex-col overflow-hidden p-5 hover:-translate-y-1 hover:border-pine-300 hover:shadow-cardhover"
    :class="promo.hot ? 'ring-1 ring-acid-300' : ''"
  >
    <!-- Discount tab in the top-right corner -->
    <div
      v-if="discount"
      class="absolute right-0 top-0 flex flex-col items-center rounded-bl-2xl bg-pine-800 px-3 py-2 text-bone-50"
    >
      <span class="nums text-lg font-bold leading-none">-{{ discount }}%</span>
      <span class="text-[0.6rem] uppercase tracking-wider text-pine-200">off</span>
    </div>

    <header class="mb-3 flex flex-wrap items-center gap-2 pr-12">
      <CategoryBadge :category="promo.category" />
      <span
        v-if="promo.hot"
        class="badge bg-acid-300 text-pine-900"
      >
        <Icon name="flame" :size="13" :stroke-width="2" /> Hot deal
      </span>
      <span
        v-if="promo.status && promo.status !== 'published'"
        class="badge bg-bone-200 text-ink-500 capitalize"
      >
        {{ promo.status }}
      </span>
    </header>

    <h3 class="font-display text-lg font-bold leading-snug tracking-tight text-ink-900">
      {{ promo.title || 'Sem título' }}
    </h3>
    <p v-if="promo.description" class="mt-1.5 line-clamp-3 text-sm leading-relaxed text-ink-500">
      {{ promo.description }}
    </p>

    <div class="mt-5 flex items-end gap-2.5">
      <span v-if="price" class="nums text-2xl font-bold tracking-tight text-pine-800">{{ price }}</span>
      <span v-if="original && discount" class="nums pb-1 text-sm text-ink-400 line-through">
        {{ original }}
      </span>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-500">
      <span v-if="promo.store" class="inline-flex items-center gap-1.5">
        <Icon name="store" :size="14" /> {{ promo.store }}
      </span>
      <span v-if="typeof promo.score === 'number'" class="inline-flex items-center gap-1.5">
        <Icon name="trending" :size="14" /> <span class="nums">{{ promo.score }}</span>
      </span>
    </div>

    <footer class="mt-5 flex items-center gap-2 border-t border-bone-200 pt-4">
      <button
        class="btn-ghost btn-sm flex-1 hover:!ring-pine-400 hover:text-pine-700"
        :disabled="voting"
        @click="emit('vote', 1)"
      >
        <Icon name="up" :size="15" /> Curtir
      </button>
      <button
        class="btn-ghost btn-sm flex-1 hover:!ring-rose-300 hover:text-rose-600"
        :disabled="voting"
        @click="emit('vote', -1)"
      >
        <Icon name="down" :size="15" /> Não curtir
      </button>
    </footer>
  </article>
</template>
