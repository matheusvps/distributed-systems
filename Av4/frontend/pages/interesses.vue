<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { usePromocoesStore } from '~/stores/promocoes'
import { useInteressesStore } from '~/stores/interesses'
import { useUserStore } from '~/stores/user'
import { useToast } from '~/composables/useToast'

const promos = usePromocoesStore()
const interesses = useInteressesStore()
const user = useUserStore()
const toast = useToast()

const pending = ref<string | null>(null)

async function load() {
  await Promise.all([
    promos.categories.length ? Promise.resolve() : promos.fetchCategories(),
    interesses.fetch(user.consumerId)
  ])
}

onMounted(load)
watch(() => user.consumerId, () => interesses.fetch(user.consumerId))

async function toggle(category: string) {
  pending.value = category
  const following = interesses.isFollowing(category)
  try {
    if (following) {
      await interesses.unfollow(user.consumerId, category)
      toast.info(`Deixou de seguir "${category}"`)
    } else {
      await interesses.follow(user.consumerId, category)
      toast.success(`Seguindo "${category}"`)
    }
  } catch (e: any) {
    toast.error(e?.data?.message || e?.message || 'Falha ao atualizar interesse')
  } finally {
    pending.value = null
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader
      eyebrow="Preferências"
      title="Meus interesses"
      :subtitle="`Categorias seguidas por ${user.consumerId} — você recebe notificações ao vivo delas.`"
    >
      <template #actions>
        <span class="badge bg-pine-50 text-pine-700 ring-1 ring-inset ring-pine-100">
          <span class="nums">{{ interesses.interests.length }}</span> seguindo
        </span>
      </template>
    </PageHeader>

    <div v-if="interesses.loading" class="card p-6 text-sm text-ink-400">Carregando…</div>

    <EmptyState
      v-else-if="!promos.categories.length"
      title="Sem categorias disponíveis"
      subtitle="O catálogo de categorias ainda não retornou dados."
    />

    <div v-else class="grid gap-3 sm:grid-cols-2">
      <div
        v-for="c in promos.categories"
        :key="c"
        class="card flex items-center justify-between gap-3 p-4"
        :class="interesses.isFollowing(c) ? 'border-pine-200 bg-pine-50/40' : ''"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-11 w-11 items-center justify-center rounded-xl transition-colors"
            :class="interesses.isFollowing(c) ? 'bg-pine-800 text-acid-300' : 'bg-bone-200 text-ink-500'"
          >
            <Icon :name="interesses.isFollowing(c) ? 'bookmark' : 'tag'" :size="20" />
          </div>
          <div>
            <p class="font-display text-sm font-bold capitalize text-ink-900">{{ c }}</p>
            <p class="text-xs text-ink-400">
              {{ interesses.isFollowing(c) ? 'Seguindo' : 'Não seguindo' }}
            </p>
          </div>
        </div>
        <button
          class="btn-sm shrink-0"
          :class="interesses.isFollowing(c) ? 'btn-ghost' : 'btn-primary'"
          :disabled="pending === c"
          @click="toggle(c)"
        >
          {{ interesses.isFollowing(c) ? 'Deixar de seguir' : 'Seguir' }}
        </button>
      </div>
    </div>
  </div>
</template>
