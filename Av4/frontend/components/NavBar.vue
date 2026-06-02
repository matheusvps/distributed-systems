<script setup lang="ts">
import { computed } from 'vue'
import { useNotificacoesStore } from '~/stores/notificacoes'

const notif = useNotificacoesStore()
const badge = computed(() => notif.unread)

const links = [
  { to: '/', label: 'Promoções', icon: '🏷️' },
  { to: '/hot-deals', label: 'Hot Deals', icon: '🔥' },
  { to: '/cadastro', label: 'Cadastrar', icon: '➕' },
  { to: '/interesses', label: 'Interesses', icon: '⭐' },
  { to: '/notificacoes', label: 'Notificações', icon: '🛎️' }
]
</script>

<template>
  <nav class="flex flex-col gap-1">
    <NuxtLink
      v-for="l in links"
      :key="l.to"
      :to="l.to"
      class="group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
      active-class="bg-brand-50 text-brand-700 hover:bg-brand-50"
    >
      <span class="text-base">{{ l.icon }}</span>
      <span class="flex-1">{{ l.label }}</span>
      <span
        v-if="l.to === '/notificacoes' && badge > 0"
        class="badge min-w-5 justify-center bg-brand-600 px-1.5 text-white"
      >
        {{ badge > 99 ? '99+' : badge }}
      </span>
    </NuxtLink>
  </nav>
</template>
