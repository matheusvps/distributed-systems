<script setup lang="ts">
import { computed } from 'vue'
import { useNotificacoesStore } from '~/stores/notificacoes'
import { useUserStore } from '~/stores/user'
import { useNotificationPanel } from '~/composables/useNotificationPanel'

const notif = useNotificacoesStore()
const user = useUserStore()
const { open, toggle } = useNotificationPanel()
const badge = computed(() => notif.unread)

const clienteLinks = [
  { to: '/', label: 'Promoções', icon: 'tag' },
  { to: '/hot-deals', label: 'Hot Deals', icon: 'flame' },
  { to: '/interesses', label: 'Interesses', icon: 'bookmark' }
]
const lojaLinks = [
  { to: '/loja', label: 'Minhas promoções', icon: 'trending' },
  { to: '/cadastro', label: 'Cadastrar', icon: 'plus' }
]
const links = computed(() => (user.role === 'loja' ? lojaLinks : clienteLinks))
</script>

<template>
  <nav class="flex flex-col gap-0.5">
    <NuxtLink
      v-for="l in links"
      :key="l.to"
      :to="l.to"
      class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-ink-700 transition-colors hover:bg-bone-200/70"
      active-class="!bg-pine-800 !text-bone-50 shadow-card hover:!bg-pine-800"
    >
      <Icon :name="l.icon" :size="18" class="opacity-80 transition-opacity group-hover:opacity-100" />
      <span class="flex-1">{{ l.label }}</span>
    </NuxtLink>

    <!-- Notificações: só para cliente; é toggle do painel, não uma rota -->
    <button
      v-if="user.role === 'cliente'"
      type="button"
      class="group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors"
      :class="open
        ? 'bg-pine-800 text-bone-50 shadow-card'
        : 'text-ink-700 hover:bg-bone-200/70'"
      @click="toggle"
    >
      <Icon name="bell" :size="18" class="opacity-80 transition-opacity group-hover:opacity-100" />
      <span class="flex-1 text-left">Notificações</span>
      <span
        v-if="badge > 0"
        class="badge nums min-w-[1.25rem] justify-center px-1.5"
        :class="open ? 'bg-bone-50 text-pine-800' : 'bg-acid-300 text-pine-900'"
      >
        {{ badge > 99 ? '99+' : badge }}
      </span>
    </button>
  </nav>
</template>
