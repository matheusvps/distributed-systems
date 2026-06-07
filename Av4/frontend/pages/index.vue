<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { usePromocoesStore } from '~/stores/promocoes'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'

const store = usePromocoesStore()
const user = useUserStore()
const toast = useToast()
const votingId = ref<string | null>(null)

async function load() {
  await store.fetchPromotions({ category: store.selectedCategory || undefined })
}

watch(() => store.selectedCategory, load)

onMounted(async () => {
  await Promise.all([store.fetchCategories(), load()])
})

async function onVote(id: string, vote: 1 | -1) {
  votingId.value = id
  try {
    await store.vote(id, vote, user.consumerId)
    toast.success(vote === 1 ? 'Voto positivo registrado' : 'Voto negativo registrado')
  } catch (e: any) {
    toast.error(e?.data?.message || e?.message || 'Não foi possível votar')
  } finally {
    votingId.value = null
  }
}
</script>

<template>
  <div>
    <PageHeader
      eyebrow="Catálogo"
      title="Promoções"
      subtitle="Descubra as melhores ofertas e ajude a impulsionar as que valem a pena com seu voto."
    >
      <template #actions>
        <button class="btn-ghost btn-sm" :disabled="store.loading" @click="load">
          <Icon name="refresh" :size="15" :class="store.loading ? 'animate-spin' : ''" /> Atualizar
        </button>
      </template>
    </PageHeader>

    <div class="mb-7">
      <CategoryFilter
        v-model="store.selectedCategory"
        :categories="store.categories"
      />
    </div>

    <div v-if="store.loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <PromoCardSkeleton v-for="n in 6" :key="n" />
    </div>

    <EmptyState
      v-else-if="store.error"
      icon="alert"
      title="Erro ao carregar"
      :subtitle="store.error"
    >
      <button class="btn-primary btn-sm mt-4" @click="load">Tentar novamente</button>
    </EmptyState>

    <EmptyState
      v-else-if="!store.items.length"
      title="Nenhuma promoção encontrada"
      subtitle="Ajuste o filtro de categoria ou cadastre a primeira oferta."
    />

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <PromoCard
        v-for="p in store.items"
        :key="p.id"
        :promo="p"
        :voting="votingId === p.id"
        @vote="(v) => onVote(p.id, v)"
      />
    </div>
  </div>
</template>
