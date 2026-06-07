<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Promotion } from '~/types'
import { useApiService } from '~/services/api'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'

const api = useApiService()
const user = useUserStore()
const toast = useToast()

const items = ref<Promotion[]>([])
const loading = ref(false)
const error = ref('')
const votingId = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getPromotions({ hot: true })
    // Defensive: filter client-side too, in case the gateway ignores the flag.
    items.value = (res?.promotions ?? []).filter((p) => p.hot !== false)
  } catch (e: any) {
    error.value = e?.data?.message || e?.message || 'Falha ao carregar hot deals'
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function onVote(id: string, vote: 1 | -1) {
  votingId.value = id
  try {
    await api.vote(id, { vote, consumerId: user.consumerId })
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
      eyebrow="Em alta"
      title="Hot Deals"
      subtitle="As ofertas com mais engajamento, impulsionadas em tempo real pelos votos da comunidade."
    >
      <template #actions>
        <button class="btn-ghost btn-sm" :disabled="loading" @click="load">
          <Icon name="refresh" :size="15" :class="loading ? 'animate-spin' : ''" /> Atualizar
        </button>
      </template>
    </PageHeader>

    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <PromoCardSkeleton v-for="n in 3" :key="n" />
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
      v-else-if="!items.length"
      icon="flame"
      title="Nenhum hot deal no momento"
      subtitle="Vote nas promoções para impulsionar as melhores ofertas ao topo."
    />

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <PromoCard
        v-for="p in items"
        :key="p.id"
        :promo="p"
        :voting="votingId === p.id"
        @vote="(v) => onVote(p.id, v)"
      />
    </div>
  </div>
</template>
