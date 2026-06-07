<script setup lang="ts">
import { computed } from 'vue'
import { useNotificacoesStore } from '~/stores/notificacoes'

const notif = useNotificacoesStore()
const badge = computed(() => notif.unread)

const links = [
  { to: '/', label: 'Promoções', icon: 'tag' },
  { to: '/hot-deals', label: 'Hot Deals', icon: 'flame' },
  { to: '/cadastro', label: 'Cadastrar', icon: 'plus' },
  { to: '/interesses', label: 'Interesses', icon: 'bookmark' },
  { to: '/notificacoes', label: 'Notificações', icon: 'bell' }
]
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
      <span
        v-if="l.to === '/notificacoes' && badge > 0"
        class="badge nums min-w-[1.25rem] justify-center bg-acid-300 px-1.5 text-pine-900"
      >
        {{ badge > 99 ? '99+' : badge }}
      </span>
    </NuxtLink>
  </nav>
</template>
